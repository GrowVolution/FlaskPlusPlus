from flask import request, render_template, url_for
from werkzeug.exceptions import NotFound
from markupsafe import Markup

from flaskpp.app.utils.translating import get_locale
from flaskpp.app.utils.auto_nav import nav_links
from flaskpp.app.socket import default_handlers, no_handler
from flaskpp.utils import random_code, enabled
from flaskpp.utils.debugger import log, exception

handlers = {}


def context_processor(fn):
    handlers["context_processor"] = fn
    return fn

@context_processor
def _context_processor():
    return dict(
        PATH=request.path,
        LANG=get_locale(),
        NAV=nav_links,

        enabled=enabled,
        fpp_tailwind=Markup(f"<link rel='stylesheet' href='{ url_for('fpp_default.static', filename='css/tailwind.css') }'>"),
        tailwind_main=Markup(f"<link rel='stylesheet' href='{ url_for('static', filename='css/tailwind.css') }'>"),
    )


def before_request(fn):
    handlers["before_request"] = fn
    return fn

@before_request
def _before_request():
    method = request.method.upper()
    path = request.path
    ip = request.remote_addr
    agent = request.headers.get("User-Agent")
    agent = agent if agent else "no-agent"

    log("request", f"{method:4} '{path:48}' from {ip:15} via ({agent}).")


def after_request(fn):
    handlers["after_request"] = fn
    return fn

@after_request
def _after_request(response):
    return response


def handle_app_error(fn):
    handlers["handle_app_error"] = fn
    return fn

@handle_app_error
def _handle_app_error(error):
    if isinstance(error, NotFound):
        return render_template("404.html"), 404

    eid = random_code()
    exception(error, f"Handling app request failed ({eid}).")
    return render_template("error.html"), 501


def socket_event_handler(fn):
    handlers["socket_event_handler"] = fn
    return fn

@socket_event_handler
def _socket_event_handler(sid: str, data: dict):
    event = data["event"]
    payload = data.get("payload")
    log("request", f"Socket event from {sid}: {event} - With data: {payload}")

    handler = default_handlers.get(event, no_handler)
    try:
        return handler(payload)
    except Exception as e:
        return handlers["handle_socket_error"](e)


def handle_socket_error(fn):
    handlers["handle_socket_error"] = fn
    return fn

@handle_socket_error
def _handle_socket_error(error):
    eid = random_code()
    exception(error, f"Handling socket event failed ({eid}).")

    return { "error": "Error while handling socket event." }
