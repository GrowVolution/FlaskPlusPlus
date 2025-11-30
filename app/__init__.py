from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from threading import Thread
from datetime import datetime
import os

from .config import CONFIG_MAP, DefaultConfig
from .utils import enabled
from .utils.processing import context_processor, before_request, after_request, handle_app_error
from .i18n import init_i18n
from modules import register_modules
from utils.debugger import start_session, log


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


def create_app(config_name: str = "default") -> Flask:
    app = Flask(__name__)
    app.config.from_object(CONFIG_MAP.get(config_name, DefaultConfig))

    start_session(enabled("DEBUG_MODE"))

    if app.config["PROXY_FIX"]:
        count = app.config["PROXY_COUNT"]
        app.wsgi_app = ProxyFix(app.wsgi_app,
                                x_for=count,
                                x_proto=count,
                                x_host=count,
                                x_port=count,
                                x_prefix=count)

    from .extensions import limiter
    limiter.init_app(app)

    app.context_processor(context_processor)
    app.before_request(before_request)
    app.after_request(after_request)
    app.errorhandler(Exception)(handle_app_error)

    ext_database = enabled("EXT_SQLALCHEMY")
    db_updater = None
    if ext_database:
        from .extensions import db, migrate
        from .data import init_models
        db.init_app(app)
        migrate.init_app(app, db)
        init_models()

        if enabled("DB_AUTOUPDATE"):
            db_updater = Thread(target=db_autoupdate, args=(app,))

    if enabled("EXT_SOCKET"):
        from .extensions import socket
        from .utils.processing import socket_event_handler, handle_socket_error
        socket.init_app(app)
        socket.on("default_event")(socket_event_handler)
        socket.on_error_default(handle_socket_error)

    if enabled("EXT_BABEL"):
        from .extensions import babel
        from .i18n import DBDomain
        from .utils.translating import set_locale
        domain = DBDomain()
        babel.init_app(app, default_domain=domain)
        app.extensions["babel_domain"] = domain
        app.route("/lang/<locale>")(set_locale)

    if enabled("EXT_FST"):
        if not ext_database:
            raise RuntimeError("For EXT_FST EXT_SQLALCHEMY extension must be enabled.")
        from flask_security import SQLAlchemyUserDatastore

        from .extensions import security, db
        from .data.fst_base import User, Role
        security.init_app(
            app,
            SQLAlchemyUserDatastore(db, User, Role)
        )

    if enabled("EXT_AUTHLIB"):
        from .extensions import oauth
        oauth.init_app(app)

    if enabled("EXT_MAILING"):
        from .extensions import mailer
        mailer.init_app(app)

    if enabled("EXT_CACHE"):
        from .extensions import cache
        cache.init_app(app)

    if enabled("EXT_API"):
        from .extensions import api
        api.init_app(app)

    if enabled("EXT_JWT_EXTENDED"):
        from .extensions import jwt
        jwt.init_app(app)

    register_modules(app)
    init_i18n(app)

    if db_updater:
        db_updater.start()

    return app
