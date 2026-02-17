from flask import Flask, request, render_template, url_for, Response
from werkzeug.exceptions import Forbidden, NotFound
from markupsafe import Markup
from typing import Callable

from flaskpp.app.utils.translating import get_locale
from flaskpp.app.utils.auto_nav import build_nav
from flaskpp.app.utils.i18n import get_locale_data
from flaskpp.utils import random_code, enabled
from flaskpp.utils.logging import log, exception

_handlers = {}


def context_processor(fn: Callable) -> Callable:
    _handlers["context_processor"] = fn
    return fn

def _context_processor() -> dict:
    return dict(
        LANG=get_locale(),
        NAV=build_nav(),

        enabled=enabled,
        fpp_tailwind=Markup(f"<link rel='stylesheet' href='{ url_for('fpp_default.static', filename='css/tailwind.css') }'>"),
        tailwind_main=Markup(f"<link rel='stylesheet' href='{ url_for('static', filename='css/tailwind.css') }'>"),
        get_locale_data=get_locale_data
    )


def before_request(fn: Callable) -> Callable:
    _handlers["before_request"] = fn
    return fn

def _before_request():
    method = request.method.upper()
    path = request.path
    ip = request.remote_addr
    agent = request.headers.get("User-Agent")
    agent = agent if agent else "no-agent"

    log(f"[REQUEST] {method:4} '{path:50}'\t\tfrom {ip:15} via ({agent}).")


def after_request(fn: Callable) -> Callable:
    _handlers["after_request"] = fn
    return fn

def _after_request(response: Response) -> Response:
    return response


def handle_app_error(fn: Callable) -> Callable:
    _handlers["handle_app_error"] = fn
    return fn

def _handle_app_error(error: Exception):
    if isinstance(error, Forbidden):
        return render_template("403.html"), 403

    if isinstance(error, NotFound):
        return render_template("404.html"), 404

    eid = random_code()
    exception(error, f"Handling app request failed ({eid}).")
    return render_template("501.html"), 501


def get_handler(name: str) -> Callable:
    handler = _handlers.get(name)
    if not handler or not callable(handler):
        if name == "context_processor":
            return _context_processor
        if name == "before_request":
            return _before_request
        if name == "after_request":
            return _after_request
        if name == "handle_app_error":
            return _handle_app_error
    return handler


def set_default_handlers(app: Flask):
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
