from flask import Flask, Blueprint, render_template as _render_template, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
from markupsafe import Markup
from threading import Thread
from datetime import datetime
from asgiref.wsgi import WsgiToAsgi
from socketio import ASGIApp
from pathlib import Path
from importlib import import_module
import os, json, re

from flaskpp.app.config import CONFIG_MAP
from flaskpp.app.config.default import DefaultConfig
from flaskpp.app.utils.processing import handlers
from flaskpp.app.i18n import init_i18n
from flaskpp.modules import register_modules, ManifestError, ModuleError
from flaskpp.tailwind import generate_tailwind_css
from flaskpp.utils import enabled
from flaskpp.utils.debugger import start_session, log, exception

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

        if self.config["RATELIMIT"]:
            from flaskpp.app.extensions import limiter
            limiter.init_app(self)

        fpp_processing = enabled("FPP_PROCESSING")
        if fpp_processing:
            set_default_handlers(self)

        ext_database = enabled("EXT_SQLALCHEMY")
        db_updater = None
        if ext_database:
            from flaskpp.app.extensions import db, migrate
            from flaskpp.app.data import init_models
            db.init_app(self)
            migrate.init_app(self, db)
            init_models()

            if enabled("DB_AUTOUPDATE"):
                db_updater = Thread(target=db_autoupdate, args=(self,))

        if enabled("EXT_SOCKET") and fpp_processing:
            from flaskpp.app.extensions import socket
            socket.on("default_event")(handlers["socket_event_handler"])

        if enabled("EXT_BABEL"):
            from flaskpp.app.extensions import babel
            from flaskpp.app.i18n import DBDomain
            from flaskpp.app.utils.translating import set_locale
            domain = DBDomain()
            babel.init_app(self, default_domain=domain)
            self.extensions["babel_domain"] = domain
            self.route("/lang/<locale>")(set_locale)

        if enabled("EXT_FST"):
            if not ext_database:
                raise RuntimeError("For EXT_FST EXT_SQLALCHEMY extension must be enabled.")
            from flask_security import SQLAlchemyUserDatastore

            from flaskpp.app.extensions import security, db
            from flaskpp.app.data.fst_base import User, Role
            security.init_app(
                self,
                SQLAlchemyUserDatastore(db, User, Role)
            )

        if enabled("EXT_AUTHLIB"):
            from flaskpp.app.extensions import oauth
            oauth.init_app(self)

        if enabled("EXT_MAILING"):
            from flaskpp.app.extensions import mailer
            mailer.init_app(self)

        if enabled("EXT_CACHE"):
            from flaskpp.app.extensions import cache
            cache.init_app(self)

        if enabled("EXT_API"):
            from flaskpp.app.extensions import api
            api.init_app(self)

        if enabled("EXT_JWT_EXTENDED"):
            from flaskpp.app.extensions import jwt
            jwt.init_app(self)

        generate_tailwind_css(self)

        self.register_blueprint(_fpp_default)
        self.url_prefix = ""
        register_modules(self)
        self.static_url_path = f"{self.url_prefix}/static"

        if enabled("FRONTEND_ENGINE"):
            from flaskpp.fpp_node.fpp_vite import Frontend
            engine = Frontend(self)
            self.context_processor(lambda: {
                "vite_main": engine.vite
            })
            self.frontend_engine = engine

        init_i18n(self)

        if db_updater:
            db_updater.start()

        self._asgi_app = None

    def to_asgi(self) -> WsgiToAsgi | ASGIApp:
        if self._asgi_app is not None:
            return self._asgi_app

        app = WsgiToAsgi(self)
        if enabled("EXT_SOCKET"):
            from flaskpp.app.extensions import socket
            self._asgi_app = ASGIApp(socket, other_asgi_app=app)
            return self._asgi_app
        self._asgi_app = app
        return app


class Module(Blueprint):
    def __init__(self, file: str, import_name: str, required_extensions: list = None):
        if not "modules." in import_name:
            raise ModuleError("Modules have to be created in the modules package.")

        self.name = import_name.split(".")[-1]
        self.import_name = import_name
        self.root_path = Path(file).parent
        manifest = self.root_path / "manifest.json"
        self.info = self._load_manifest(manifest)
        self.safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", self.name)
        self.extensions = required_extensions or []
        self.context = {
            "NAME": self.safe_name,
        }
        self.home = False

        from flaskpp.app.extensions import require_extensions
        self.enable = require_extensions(*self.extensions)(self._enable)

        super().__init__(
            self.safe_name,
            import_name,
            static_folder=(Path(self.root_path) / "static")
        )

    def __repr__(self):
        return f"<{self.info['name']} {self.version}> {self.info.get('description', '')}"

    def _enable(self, app: FlaskPP, home: bool):
        if home:
            self.static_url_path = "/static"
            app.url_prefix = "/app"
            self.home = True
        else:
            self.url_prefix = f"/{self.safe_name}"
            self.static_url_path = f"/{self.safe_name}/static"

        try:
            routes = import_module(f"{self.import_name}.routes")
            init = getattr(routes, "init_routes", None)
            if not init:
                raise ImportError("Missing init function in routes.")
            init(self)
        except (ModuleNotFoundError, ImportError, TypeError) as e:
            log("warn", f"Failed to register routes for {self.name}: {e}")

        if "sqlalchemy" in self.extensions:
            try:
                data = import_module(f"{self.import_name}.data")
                init = getattr(data, "init_models", None)
                if not init:
                    raise ImportError("Missing init function in data.")
                init()
            except (ModuleNotFoundError, ImportError, TypeError) as e:
                log("warn", f"Failed to initialize models for {self.name}: {e}")

        if enabled("FRONTEND_ENGINE"):
            from flaskpp.fpp_node.fpp_vite import Frontend
            engine = Frontend(self)
            self.context["vite"] = engine.vite
            self.frontend_engine = engine

        self.context_processor(lambda: dict(
            **self.context,
            tailwind=Markup(f"<link rel='stylesheet' href='{url_for(f'{self.safe_name}.static', filename='css/tailwind.css')}'>")
        ))
        app.register_blueprint(self)

    def _load_manifest(self, manifest: Path) -> dict:
        if not manifest.exists():
            raise FileNotFoundError(f"Manifest file for {self.name} not found.")

        try:
            module_data = json.loads(manifest.read_text())
        except json.decoder.JSONDecodeError:
            raise ManifestError(f"Invalid format for manifest of {self.name}.")

        if not "name" in module_data:
            module_data["name"] = self.name
        else:
            self.name = module_data["name"]

        if not "description" in module_data:
            log("warn", f"Missing description of {module_data['name']}.")

        if not "version" in module_data:
            raise ManifestError("Module version not defined.")

        if not "author" in module_data:
            log("warn", f"Author of {module_data['name']} not defined.")

        return module_data

    @property
    def version(self) -> str:
        version_str = self.info.get("version", "").lower().strip()
        if not version_str:
            raise ManifestError("Module version not defined.")

        if " " in version_str and not (version_str.endswith("alpha") or version_str.endswith("beta")):
            raise ManifestError("Invalid version string format.")

        if version_str.startswith("v"):
            version_str = version_str[1:]

        try:
            v_numbers = version_str.split(" ")[0].split(".")
            if len(v_numbers) > 3:
                raise ManifestError("Too many version numbers.")

            for v_number in v_numbers:
                int(v_number)
        except ValueError:
            raise ManifestError("Invalid version numbers.")

        return version_str

    def render_template(self, template: str, **context) -> str:
        render_name = template if self.home else f"{self.safe_name}/{template}"
        return _render_template(render_name, **context)
