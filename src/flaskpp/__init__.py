from flask import Flask, Blueprint, render_template as _render_template, url_for, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix
from markupsafe import Markup
from threading import Thread, Event
from datetime import datetime
from asgiref.wsgi import WsgiToAsgi
from socketio import ASGIApp
from pathlib import Path
from importlib import import_module
from typing import Callable
from types import FrameType
import os, json, re, signal

from flaskpp.app.config import CONFIG_MAP
from flaskpp.app.config.default import DefaultConfig
from flaskpp.app.utils.processing import get_handler
from flaskpp.i18n import init_i18n
from flaskpp.modules import register_modules, version_check
from flaskpp.tailwind import generate_tailwind_css
from flaskpp.utils import enabled, takes_arg, required_arg_count
from flaskpp.utils.debugger import start_session, log, exception
from flaskpp.exceptions import ManifestError, ModuleError, EventHookException

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
    app.context_processor(
        lambda: get_handler("context_processor")()
    )
    app.before_request(
        lambda : get_handler("before_request")()
    )
    app.after_request(
        lambda response: get_handler("after_request")(response)
    )
    app.errorhandler(Exception)(
        lambda error: get_handler("handle_app_error")(error)
    )


class FlaskPP(Flask):
    def __init__(self, import_name: str, config_name: str):
        super().__init__(
            import_name,
            static_folder=None,
            static_url_path=None
        )
        self.name = re.sub(r"[^a-zA-Z0-9_-]", "_", os.getenv("APP_NAME", self.import_name)).lower()
        self.config.from_object(CONFIG_MAP.get(config_name, DefaultConfig))

        self._startup_hooks = []
        self._shutdown_hooks = []

        if self.config["PROXY_FIX"]:
            count = self.config["PROXY_COUNT"]
            self.wsgi_app = ProxyFix(
                self.wsgi_app,
                x_for=count,
                x_proto=count,
                x_host=count,
                x_port=count,
                x_prefix=count
            )

        from flaskpp.app.extensions import limiter
        limiter.init_app(self)

        if enabled("FPP_PROCESSING"):
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

        if enabled("EXT_SOCKET"):
            from flaskpp.app.extensions import socket
            socket.init_app(self)

        if enabled("EXT_BABEL"):
            from flaskpp.app.extensions import babel
            from flaskpp.app.utils.translating import set_locale
            babel.init_app(self)
            self.route("/lang/<locale>")(set_locale)

            if enabled("FPP_I18N_FALLBACK") and ext_database:
                from flaskpp.app.data.noinit_translations import setup_db
                self.on_startup(setup_db)

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

        self.url_prefix = None
        self.frontend_engine = None

        init_i18n(self)

        if db_updater:
            db_updater.start()

        self._asgi_app = None
        self._server = Thread(target=self._run_server, daemon=True)
        self._shutdown_flag = Event()

    def to_asgi(self) -> WsgiToAsgi | ASGIApp:
        if self._asgi_app is not None:
            return self._asgi_app

        wsgi = WsgiToAsgi(self)

        if enabled("EXT_SOCKET"):
            from flaskpp.app.extensions import socket
            app = ASGIApp(socket, other_asgi_app=wsgi)
        else:
            app = wsgi

        self._asgi_app = app
        return self._asgi_app

    def on_startup(self, fn: Callable) -> Callable:
        if required_arg_count(fn) > 0:
            raise EventHookException("Startup hooks must not receive non optional arguments.")
        self._startup_hooks.append(fn)
        return fn

    def on_shutdown(self, fn: Callable) -> Callable:
        if required_arg_count(fn) > 0:
            raise EventHookException("Shutdown hooks must not receive non optional arguments.")
        self._shutdown_hooks.append(fn)
        return fn

    def _startup(self):
        with self.app_context():
            log("info", "Running startup hooks...")
            [hook() for hook in self._startup_hooks]

    def _shutdown(self):
        with self.app_context():
            log("info", "Running shutdown hooks...")
            [hook() for hook in self._shutdown_hooks]

    def _run_server(self):
        import uvicorn
        uvicorn.run(
            self.to_asgi(),
            host="0.0.0.0",
            port=int(os.getenv("SERVER_PORT", "5000")),
            log_level="debug" if enabled("DEBUG_MODE") else "info",
        )

    def _handle_shutdown(self, signum: int, frame: FrameType):
        log("info", f"Handling signal {'SIGINT' if signum == signal.SIGINT else 'SIGTERM'}: Shutting down...")
        if self._shutdown_flag.is_set():
            return
        self._shutdown_flag.set()

    def start(self):
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

        start_session(enabled("DEBUG_MODE"))

        if enabled("AUTOGENERATE_TAILWIND_CSS"):
            generate_tailwind_css(self)

        if enabled("FPP_MODULES"):
            self.register_blueprint(_fpp_default)
            self.url_prefix = ""
            register_modules(self)
            self.static_url_path = f"{self.url_prefix}/static"
            self.add_url_rule(
                f"{self.static_url_path}/<path:filename>",
                endpoint="static",
                view_func=lambda filename: send_from_directory(Path(self.root_path) / "static", filename)
            )

        if enabled("FRONTEND_ENGINE"):
            from flaskpp.fpp_node.fpp_vite import Frontend
            engine = Frontend(self)
            self.context_processor(lambda: {
                "vite_main": engine.vite
            })
            self.frontend_engine = engine

        self._startup()
        self._server.start()
        self._shutdown_flag.wait()
        self._shutdown()


class Module(Blueprint):
    def __init__(self, file: str, import_name: str, required_extensions: list = None,
                 init_routes_on_enable: bool = True):
        if not "modules." in import_name:
            raise ModuleError("Modules have to be created in the modules package.")

        self.module_name = import_name.split(".")[-1]
        self.import_name = import_name
        self.root_path = Path(file).parent
        manifest = self.root_path / "manifest.json"
        self.info = self._load_manifest(manifest)
        safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", self.module_name).lower()
        self.required_extensions = required_extensions or []
        self.context = {
            "NAME": safe_name,
        }
        self.home = False

        from flaskpp.utils import require_extensions
        self.enable = require_extensions(*self.required_extensions)(self._enable)
        self._on_enable = None
        self._init_routes = init_routes_on_enable

        super().__init__(
            safe_name,
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
            self.url_prefix = f"/{self.name}"
            self.static_url_path = f"/{self.name}/static"

        if self._init_routes:
            self.init_routes()

        if "sqlalchemy" in self.required_extensions:
            try:
                data = import_module(f"{self.import_name}.data")
                init = getattr(data, "init_models", None)
                if not init:
                    raise ImportError("Missing init function in data.")
                init()
            except (ModuleNotFoundError, ImportError, TypeError) as e:
                log("warn", f"Failed to initialize models for {self.module_name}: {e}")

        if enabled("FRONTEND_ENGINE"):
            from flaskpp.fpp_node.fpp_vite import Frontend
            engine = Frontend(self)
            self.context["vite"] = engine.vite
            self.frontend_engine = engine

        self.context_processor(lambda: dict(
            **self.context,
            tailwind=Markup(f"<link rel='stylesheet' href='{url_for(f'{self.name}.static', filename='css/tailwind.css')}'>")
        ))

        if self._on_enable is not None:
            self._on_enable(app)

        app.register_blueprint(self)

    def _load_manifest(self, manifest: Path) -> dict:
        if not manifest.exists():
            raise FileNotFoundError(f"Manifest file for {self.module_name} not found.")

        try:
            module_data = json.loads(manifest.read_text())
        except json.decoder.JSONDecodeError:
            raise ManifestError(f"Invalid format for manifest of {self.module_name}.")

        if not "name" in module_data:
            module_data["name"] = self.module_name
        else:
            self.module_name = module_data["name"]

        if not "description" in module_data:
            log("warn", f"Missing description of {module_data['name']}.")

        if not "version" in module_data:
            raise ManifestError("Module version not defined.")

        if not "author" in module_data:
            log("warn", f"Author of {module_data['name']} not defined.")

        return module_data

    @property
    def version(self) -> str:
        check = version_check(self.info.get("version", ""))
        if not check[0]:
            raise ManifestError(check[1])

        return check[1]

    def init_routes(self):
        try:
            routes = import_module(f"{self.import_name}.routes")
            init = getattr(routes, "init_routes", None)
            if not init:
                raise ImportError("Missing init function in routes.")
            init(self)
        except (ModuleNotFoundError, ImportError, TypeError) as e:
            log("warn", f"Failed to register routes for {self.module_name}: {e}")

    def wrap_message(self, message: str) -> str:
        domain = self.context.get("DOMAIN")
        if not domain:
            return message
        return f"{message}@{domain}"

    def t(self, message: str) -> str:
        from flaskpp.app.utils.translating import t
        return t(self.wrap_message(message), False)

    def tn(self, singular: str, plural: str, n: int) -> str:
        from flaskpp.app.utils.translating import tn
        return tn(self.wrap_message(singular), plural, n, False)

    def render_template(self, template: str, **context) -> str:
        render_name = template if self.home else f"{self.name}/{template}"

        return _render_template(render_name, **context)

    def on_enable(self, fn: Callable) -> Callable:
        if not takes_arg(fn, "app") or required_arg_count(fn) != 1:
            raise EventHookException(f"{self.import_name}.on_enable must take exactly one non optional argument: 'app'.")
        self._on_enable = fn
        return fn
