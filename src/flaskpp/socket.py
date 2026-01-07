from socketio import AsyncServer
from werkzeug.http import parse_accept_header
from werkzeug.datastructures import LanguageAccept
from contextvars import ContextVar
from http.cookies import SimpleCookie
from typing import Callable, Any, TYPE_CHECKING

from flaskpp.utils import enabled, random_code, async_result, decorate
from flaskpp.utils.debugger import log, exception

if TYPE_CHECKING:
    from flaskpp import FlaskPP


class _EventContext:
    def __init__(self, ctx: ContextVar, session: dict):
        self.ctx = ctx
        self.session = session

    def __enter__(self):
        self.token = self.ctx.set(self)
        return self

    def __exit__(self, *args):
        self.ctx.reset(self.token)


class FppSocket(AsyncServer):
    def __init__(self, app: "FlaskPP" = None, default_processing: bool = False,
                 default_event_name: str = "default_event",
                 enable_sid_passing: bool = True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = None
        self._context = None

        self.default_processing = default_processing or enabled("FPP_PROCESSING")
        self._default_event_name = default_event_name
        self.sid_passing = enable_sid_passing
        self._connect_handler = None
        self._default_handler = None
        self._default_handlers = {}
        self._html_injector = None
        self._html_injectors = {}
        self._error_handler = None

        if app is not None:
            self.init_app(app)

    def _event_context(self, session: dict) -> _EventContext:
        return _EventContext(self._context, session)

    async def _on_connect(self, sid: str, environ: dict):
        if self.app is None:
            RuntimeError("Cannot establish connection: 'app' is None. Did you run init_app(app)?")

        cookies = _get_cookies(environ)
        accept_lang = _get_accept_languages(environ)

        if accept_lang:
            with self.app.app_context():
                from flaskpp.app.utils.translating import supported_locales
                fallback = accept_lang.best_match(supported_locales())
        else:
            fallback = None

        await self.save_session(sid, {
            "session": cookies.get("session"),
            "lang": cookies.get("lang", fallback),
        })

    async def _on_default(self, sid: str, data: dict) -> Any:
        event = data["event"]
        payload = data.get("payload")

        event, namespace = resolve_namespace(event)
        log("request", f"Socket event from {sid}: {event}@{namespace} - With data: {payload}")
        def no_handler(*_): raise NotImplementedError(f"Socket event handler {event}@{namespace} not found.")

        handler = self.get_handler(event, namespace) or no_handler
        return await async_result(handler(sid, payload))

    async def _html_inject(self, key: str) -> str:
        key, namespace = resolve_namespace(key)
        def no_injector(): raise NotImplementedError(f"Html injector {key}@{namespace} not found.")

        handler = self.get_handler(key, namespace, "html") or no_injector
        html = await async_result(handler())
        if html is None or not isinstance(html, str):
            raise ValueError(f"Html injector for {key}@{namespace} did not return valid html.")

        return html

    def _ensure_namespace_accepted(self, namespace: str):
        if namespace != "*" and namespace not in self.namespaces:
            self.namespaces.append(namespace)

    def init_app(self, app):
        self.app = app
        self._context = ContextVar(f"{app.name}_socket")

        if self.default_processing:
            if self._connect_handler is None:
                self._connect_handler = self._on_connect
            if self._default_handler is None:
                self._default_handler = self._on_default
            if self._html_injector is None:
                self._html_injector = self._html_inject
            if self._error_handler is None:
                self._error_handler = _handle_error

            self.on("connect", self._connect_handler)
            self.on(self._default_event_name, self._default_handler)
            self.on_default("html", self._html_injector)

    def on(self, event: str, handler: Callable = None, namespace: str = None) -> Callable:
        namespace = namespace or "/"
        self._ensure_namespace_accepted(namespace)

        if event == self._default_event_name:
            pass_sid = True
        else:
            pass_sid = self.sid_passing

        def decorator(fn):
            async def wrapper(*args):
                ns = namespace
                if namespace == "*":
                    ns, sid, payload = args
                else:
                    sid, payload = args

                async with self.session(sid) as s:
                    s["__namespace__"] = ns
                    with self._event_context(s):
                        try:
                            result = fn(sid, payload) if pass_sid else fn(payload)
                            result = await async_result(result)

                        except Exception as e:
                            if not self.default_processing:
                                raise e
                            result = self._error_handler(e)
                            result = await async_result(result)

                        return result

            if namespace not in self.handlers:
                self.handlers[namespace] = {}
            self.handlers[namespace][event] = wrapper if event != "connect" else fn
            return wrapper

        return decorate(decorator, handler)

    def on_default(self, event: str, handler: Callable = None, namespace: str = None,
                   pass_sid: bool = False, **test_request_ctx) -> Callable:
        if not self.default_processing:
            raise RuntimeError("Cannot register default events: 'default_processing' is not enabled.")

        namespace = namespace or "*"

        def decorator(fn):
            async def wrapper(sid, payload):
                with self.app.app_context():
                    with self.app.test_request_context(**test_request_ctx):
                        result = fn(sid, payload) if pass_sid else fn(payload)
                        return await async_result(result)

            if namespace not in self._default_handlers:
                self._default_handlers[namespace] = {}
            self._default_handlers[namespace][event] = wrapper
            return wrapper

        return decorate(decorator, handler)

    def html_injector(self, key: str, injector: Callable = None, namespace: str = None) -> Callable:
        if not self.default_processing:
            raise RuntimeError("Cannot register html injectors: 'default_processing' is not enabled.")

        namespace = namespace or "*"

        def decorator(fn):
            if namespace not in self._html_injectors:
                self._html_injectors[namespace] = {}
            self._html_injectors[namespace][key] = fn
            return fn

        return decorate(decorator, injector)

    def on_error(self, handler: Callable = None) -> Callable:
        if not self.default_processing:
            raise RuntimeError("Cannot register Errorhandler: 'default_processing' is not enabled.")

        def decorator(fn):
            self._error_handler = fn
            return fn

        return decorate(decorator, handler)

    def connect_handler(self, handler: Callable = None) -> Callable:
        if not self.default_processing:
            raise RuntimeError("Cannot update default connect handler: 'default_processing' is not enabled.")

        def decorator(fn):
            self._connect_handler = fn
            return fn

        return decorate(decorator, handler)

    def default_handler(self, handler: Callable = None) -> Callable:
        if not self.default_processing:
            raise RuntimeError(f"Cannot register '{self._default_event_name}' handler: 'default_processing' is not enabled.")

        def decorator(fn):
            self._default_handler = fn
            return fn

        return decorate(decorator, handler)

    def html_handler(self, injector: Callable = None) -> Callable:
        if not self.default_processing:
            raise RuntimeError("Cannot register default html injector: 'default_processing' is not enabled.")

        def decorator(fn):
            self._html_injector = fn
            return fn

        return decorate(decorator, injector)

    def get_handler(self, name: str, namespace: str = None, event_type: str = "default") -> Callable:
        namespace = namespace or "/"

        def get(s, k, ns):
            h = s.get(ns, {}).get(k)
            if h: return h
            k = "*"
            return s.get(ns, {}).get(k)

        if event_type == "default":
            store = self._default_handlers
        elif event_type == "html":
            store = self._html_injectors
        else:
            store = self.handlers

        handler = get(store, name, namespace)
        if handler or namespace == "*": return handler

        namespace = "*"
        return get(store, name, namespace)

    @property
    def event_context(self) -> _EventContext | None:
        if self._context is None:
            return None
        return self._context.get()

    @property
    def current_session(self) -> dict | None:
        try:
            ctx = self.event_context
            return ctx.session if ctx else None
        except LookupError:
            return None


def resolve_namespace(name: str) -> tuple[str, str]:
    if "@" in name:
        name, namespace = name.split("@", 1)
    else:
        namespace = "*"
    return name, namespace


def _get_cookies(environ: dict) -> dict:
    scope = environ.get("asgi.scope")
    if scope:
        headers = scope.get("headers", [])
        for key, value in headers:
            if key == b"cookie":
                cookie = SimpleCookie()
                cookie.load(value.decode())
                return {k: v.value for k, v in cookie.items()}

    raw = environ.get("HTTP_COOKIE")
    if raw:
        cookie = SimpleCookie()
        cookie.load(raw)
        return {k: v.value for k, v in cookie.items()}

    return {}


def _parse_accept_language(header_value: str) -> LanguageAccept:
    return parse_accept_header(
        header_value,
        LanguageAccept
    )


def _get_accept_languages(environ: dict) -> LanguageAccept | None:
    scope = environ.get("asgi.scope")
    if scope:
        for key, value in scope.get("headers", []):
            if key == b"accept-language":
                return _parse_accept_language(value.decode())

    raw = environ.get("HTTP_ACCEPT_LANGUAGE")
    if raw:
        return _parse_accept_language(raw)

    return None


def _handle_error(error: Exception) -> dict:
    eid = random_code()
    exception(error, f"Handling socket event failed ({eid}).")

    return { "error": "Error while handling socket event.", "eid": eid }
