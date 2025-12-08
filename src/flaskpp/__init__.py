from flask import Flask, Blueprint
from werkzeug.middleware.proxy_fix import ProxyFix
from threading import Thread
from datetime import datetime
from asgiref.wsgi import WsgiToAsgi
from pathlib import Path
import os

from flaskpp.app.config import CONFIG_MAP
from flaskpp.app.config.default import DefaultConfig
from flaskpp.app.utils.processing import handlers
from flaskpp.app.i18n import init_i18n
from flaskpp.modules import register_modules
from flaskpp.utils import enabled
from flaskpp.utils.debugger import start_session, log

_fpp_default = Blueprint("fpp_default", __name__,
                         static_folder=(Path(__file__).parent / "app" / "static").resolve(),
                         static_url_path="/fpp-static")


def _fix_missing(migrations):
    versions_path = os.path.join(migrations, "versions")
    if os.path.isdir(versions_path):
        files = sorted(
            [f for f in os.listdir(versions_path) if f.endswith(".py")],
            key=lambda x: os.path.getmtime(os.path.join(versions_path, x)),
        )
        if files:
            latest_file = os.path.join(versions_path, files[-1])
            with open(latest_file, "r", encoding="utf-8") as f:
                content = f.read()

            import_str = f"import flask_security"
            if "flask_security" in content and import_str not in content:
                content = f"{import_str}\n{content}"
                with open(latest_file, "w", encoding="utf-8") as f:
                    f.write(content)
                log("migrate", f"Fixed missing flask_security import in {latest_file}")


def db_autoupdate(app):
    message = f"App-Factory autoupdate - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    with app.app_context():
        from flask_migrate import init as fm_init, migrate as fm_migrate, upgrade as fm_upgrade
        migrations = os.path.join(app.root_path, "migrations")
        if not os.path.isdir(migrations):
            fm_init(directory=migrations)
        fm_migrate(message=message, directory=migrations)

        _fix_missing(migrations)
        fm_upgrade(directory=migrations)


def set_default_handlers(app):
    app.context_processor(handlers["context_processor"])
    app.before_request(handlers["before_request"])
    app.after_request(handlers["after_request"])
    app.errorhandler(Exception)(handlers["handle_app_error"])


class FlaskPP(Flask):
    def __init__(self, import_name: str, config_name: str):
        super().__init__(import_name)
        self.config.from_object(CONFIG_MAP.get(config_name, DefaultConfig))

        start_session(enabled("DEBUG_MODE"))

        if self.config["PROXY_FIX"]:
            count = self.config["PROXY_COUNT"]
            self.wsgi_app = ProxyFix(self.wsgi_app,
                                    x_for=count,
                                    x_proto=count,
                                    x_host=count,
                                    x_port=count,
                                    x_prefix=count)

        from .app.extensions import limiter
        limiter.init_app(self)

        fpp_processing = enabled("FPP_PROCESSING")
        if fpp_processing:
            set_default_handlers(self)

        ext_database = enabled("EXT_SQLALCHEMY")
        db_updater = None
        if ext_database:
            from .app.extensions import db, migrate
            from .app.data import init_models
            db.init_app(self)
            migrate.init_app(self, db)
            init_models()

            if enabled("DB_AUTOUPDATE"):
                db_updater = Thread(target=db_autoupdate, args=(self,))

        if enabled("EXT_SOCKET"):
            from .app.extensions import socket
            socket.init_app(self)

            if fpp_processing:
                socket.on("default_event")(handlers["socket_event_handler"])
                socket.on_error_default(handlers["handle_socket_error"])

        if enabled("EXT_BABEL"):
            from .app.extensions import babel
            from .app.i18n import DBDomain
            from .app.utils.translating import set_locale
            domain = DBDomain()
            babel.init_app(self, default_domain=domain)
            self.extensions["babel_domain"] = domain
            self.route("/lang/<locale>")(set_locale)

        if enabled("EXT_FST"):
            if not ext_database:
                raise RuntimeError("For EXT_FST EXT_SQLALCHEMY extension must be enabled.")
            from flask_security import SQLAlchemyUserDatastore

            from .app.extensions import security, db
            from .app.data.fst_base import UserBase, RoleBase
            security.init_app(
                self,
                SQLAlchemyUserDatastore(db, UserBase, RoleBase)
            )

        if enabled("EXT_AUTHLIB"):
            from .app.extensions import oauth
            oauth.init_app(self)

        if enabled("EXT_MAILING"):
            from .app.extensions import mailer
            mailer.init_app(self)

        if enabled("EXT_CACHE"):
            from .app.extensions import cache
            cache.init_app(self)

        if enabled("EXT_API"):
            from .app.extensions import api
            api.init_app(self)

        if enabled("EXT_JWT_EXTENDED"):
            from .app.extensions import jwt
            jwt.init_app(self)

        self.register_blueprint(_fpp_default)
        register_modules(self)

        init_i18n(self)

        if db_updater:
            db_updater.start()

    def to_asgi(self) -> WsgiToAsgi:
        return WsgiToAsgi(self)
