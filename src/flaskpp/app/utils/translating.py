from flask import (current_app, has_app_context, has_request_context,
                   request, Response, make_response, redirect)
from urllib.parse import urlparse, urljoin

from flaskpp.i18n import DBDomain
from flaskpp.babel import valid_state
from flaskpp.utils import enabled
from flaskpp.app.extensions import socket
from flaskpp.exceptions import I18nError


def _t(s: str, wrap: bool = None) -> str:
    return s


def _tn(s: str, p: str, n: int, wrap: bool = None) -> str:
    return p if (n != 1) else s


def _wrapped_message(msg: str) -> str:
    if has_request_context() and request.blueprint:
        state = valid_state()
        module = state.module_domains.get(request.blueprint)
        if not module:
            return msg
        return module.wrap_message(msg)
    return msg


def _get_domain_data(msg: str) -> tuple[DBDomain, str, str]:
    domain = valid_state().domain
    if not isinstance(domain, DBDomain):
        raise I18nError("Flask++ translating only works with flaskpp.app.i18n.DBDomain")

    if "@" in msg:
        msg, domain_str = msg.split("@", 1)
    else:
        domain_str = domain.domain

    return domain, msg, domain_str


def _is_safe_path(path: str) -> bool:
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, path))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


def _gettext(translations, msg: str, *args) -> str:
    if len(args) > 0:
        return translations.ngettext(msg, *args)
    return translations.gettext(msg)


def _get_fallbacks() -> list[str]:
    state = valid_state()
    fallbacks = []

    if isinstance(state.fallback_domain, tuple):
        fallbacks.append(state.fallback_domain[0])

    fallbacks.append("")

    if state.fpp_fallback_domain is not None:
        fallbacks.append(state.fpp_fallback_domain)

    return fallbacks


def _fallback_escalated_text(msg: str, *args) -> str:
    domain, msg, domain_str = _get_domain_data(msg)
    translations = domain.get_translations(domain_str)
    text = _gettext(translations, msg, *args)

    fallbacks = _get_fallbacks()
    index = 0
    while text == msg and index < len(fallbacks):
        fallback = fallbacks[index].strip()
        translations = domain.get_translations(fallback)
        text = _gettext(translations, msg, *args)
        index += 1

    return text


def supported_locales() -> list[str]:
    raw = current_app.config.get("SUPPORTED_LOCALES")
    if raw:
        return raw.split(";")
    return [current_app.config.get("BABEL_DEFAULT_LOCALE", "en")]


def get_locale() -> str:
    if not has_app_context():
        raise I18nError("Failed to retreive locale: Working outside of application context.")

    default = current_app.config.get("BABEL_DEFAULT_LOCALE", "en")

    session = socket.current_session
    if session:
        return session["lang"] or default

    if has_request_context():
        return (request.cookies.get("lang") or
                request.accept_languages.best_match(supported_locales()) or
                default)
    else:
        return default


def set_locale(locale: str) -> Response:
    path = request.args.get("path", "/")
    if not _is_safe_path(path):
        path = "/"

    back = redirect(path)
    if locale not in supported_locales():
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
    def t(message: str, wrap: bool = True) -> str:
        if not has_app_context():
            return _t(message)
        if wrap:
            message = _wrapped_message(message)
        return _fallback_escalated_text(message)

    def tn(singular: str, plural: str, n: int, wrap: bool = True) -> str:
        if not has_app_context():
            return _tn(singular, plural, n)
        if wrap:
            singular = _wrapped_message(singular)
        return _fallback_escalated_text(singular, plural, n)
else:
    t = _t
    tn = _tn
