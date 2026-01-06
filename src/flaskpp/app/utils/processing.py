from flask import Flask, request, render_template, url_for, Response
from werkzeug.exceptions import NotFound
from markupsafe import Markup
from typing import Callable

from flaskpp.app.data.noinit_translations import get_locale_data
from flaskpp.app.utils.translating import get_locale
from flaskpp.app.utils.auto_nav import nav_links
from flaskpp.utils import random_code, enabled
from flaskpp.utils.debugger import log, exception

_handlers = {}


def context_processor(fn: Callable) -> Callable:
    _handlers["context_processor"] = fn
    return fn

@context_processor
def _context_processor() -> dict:
    return dict(
        PATH=request.path,
        LANG=get_locale(),
        NAV=nav_links,

        enabled=enabled,
        fpp_tailwind=Markup(f"<link rel='stylesheet' href='{ url_for('fpp_default.static', filename='css/tailwind.css') }'>"),
        tailwind_main=Markup(f"<link rel='stylesheet' href='{ url_for('static', filename='css/tailwind.css') }'>"),
        get_locale_data=get_locale_data
    )


def before_request(fn: Callable) -> Callable:
    _handlers["before_request"] = fn
    return fn

@before_request
def _before_request():
    method = request.method.upper()
    path = request.path
    ip = request.remote_addr
    agent = request.headers.get("User-Agent")
    agent = agent if agent else "no-agent"

    log("request", f"{method:4} '{path:48}' from {ip:15} via ({agent}).")


def after_request(fn: Callable) -> Callable:
    _handlers["after_request"] = fn
    return fn

@after_request
def _after_request(response: Response) -> Response:
    return response


def handle_app_error(fn: Callable) -> Callable:
    _handlers["handle_app_error"] = fn
    return fn

@handle_app_error
def _handle_app_error(error: Exception):
    if isinstance(error, NotFound):
        return render_template("404.html"), 404

    eid = random_code()
    exception(error, f"Handling app request failed ({eid}).")
    return render_template("error.html"), 501


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
