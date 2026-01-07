from flask import Flask, Blueprint, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix
from threading import Thread, Event
from asgiref.wsgi import WsgiToAsgi
from socketio import ASGIApp
from pathlib import Path
from importlib.metadata import version as _version
from typing import Callable, TYPE_CHECKING
import os, signal

from flaskpp.i18n import init_i18n
from flaskpp.tailwind import generate_tailwind_css
from flaskpp.modules import register_modules
from flaskpp.utils import enabled, required_arg_count, safe_string
from flaskpp.utils.debugger import start_session, log
from flaskpp.app.config import CONFIG_MAP
from flaskpp.app.config.default import DefaultConfig
from flaskpp.app.data import db_autoupdate
from flaskpp.app.utils.processing import set_default_handlers
from flaskpp.exceptions import EventHookException

if TYPE_CHECKING:
    from types import FrameType


class FppVersion(tuple):
    def __new__(cls, major: int, minor: int, patch: int):
        return super().__new__(cls, (major, minor, patch))

    def __str__(self):
        return f"v{'.'.join(map(str, self))}"


class FlaskPP(Flask):
    def __init__(self, import_name: str, config_name: str):
        super().__init__(
            import_name,
            static_folder=None,
            static_url_path=None
        )
        self.name = safe_string(os.getenv("APP_NAME", self.import_name)).lower()
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

    def _handle_shutdown(self, signum: int, frame: "FrameType"):
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

        from flaskpp import _fpp_root
        _fpp_default = Blueprint(
            "fpp_default", __name__,
                 static_folder=_fpp_root / "app" / "static",
                 static_url_path="/fpp-static"
        )
        self.register_blueprint(_fpp_default)

        if enabled("FPP_MODULES"):
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
                "vite_main": engine.vite,
                "vite_main_prefix": engine.prefix,
            })
            self.frontend_engine = engine
            self.on_shutdown(engine.shutdown)

        self._startup()
        self._server.start()
        self._shutdown_flag.wait()
        self._shutdown()


def version() -> FppVersion:
    v_str = _version("flaskpp").split(" ")[-1].lstrip("v")
    return FppVersion(*map(int, v_str.split(".")))
