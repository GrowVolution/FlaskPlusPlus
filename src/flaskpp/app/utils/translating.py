from flask import (current_app, has_app_context, has_request_context,
                   request, Response, make_response, redirect)
from urllib.parse import urlparse, urljoin

from ..socket import default_event
from ...utils import enabled


def _t(s: str) -> str:
    return s


def _tn(s: str, p: str, n: int) -> str:
    return p if (n != 1) else s


def _get_domain():
    return current_app.extensions["babel_domain"]


def _supported_locales() -> list[str]:
    raw = current_app.config.get("SUPPORTED_LOCALES")
    if raw:
        return raw.split(";")
    return [current_app.config.get("BABEL_DEFAULT_LOCALE", "en")]


def _is_safe_path(path: str) -> bool:
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, path))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


def get_locale() -> str:
    default = current_app.config.get("BABEL_DEFAULT_LOCALE", "en")
    if has_request_context():
        return (request.cookies.get("lang") or
                request.accept_languages.best_match(_supported_locales()) or
                default)
    else:
        return default


def set_locale(locale: str) -> Response:
    path = request.args.get("path", "/")
    if not _is_safe_path(path):
        path = "/"

    back = redirect(path)
    if locale not in _supported_locales():
        return back

    response = make_response(back)
    response.set_cookie(
        "lang",
        locale,
        max_age=60*60*24*365,
        samesite="Lax",
        secure=not enabled("DEBUG_MODE"),
        httponly=False
    )
    return response


if enabled("EXT_BABEL"):
    def t(message, **variables):
        if not has_app_context():
            return _t(message)
        return _get_domain().get_translations().gettext(message, **variables)

    def tn(singular, plural, n, **variables):
        if not has_app_context():
            return _tn(singular, plural, n)
        return _get_domain().get_translations().ngettext(singular, plural, n, **variables)
else:
    t = _t
    tn = _tn


@default_event("_")
def socket_t(key: str):
    return t(key)


@default_event("_n")
def socket_tn(data: dict):
    return tn(
        data.get("s", ""),
        data.get("p", ""),
        data.get("n", 0)
    )
