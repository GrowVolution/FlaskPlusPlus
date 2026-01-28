from pathlib import Path
from importlib import import_module
from flask_security.forms import LoginForm, RegisterFormV2
from flask_mailman import EmailMessage
from threading import Thread
from typing import Callable, TYPE_CHECKING

from flaskpp.modules import installed_modules
from flaskpp.utils import check_priority, build_sorted_tuple, enabled

if TYPE_CHECKING:
    from flaskpp import FlaskPP

_login_forms: dict[int, list[type]] = {}
_register_forms: dict[int, list[type]] = {}


def init_forms(app: "FlaskPP"):
    modules = Path(app.root_path) / "modules"

    if not modules.exists() or not modules.is_dir():
        return

    for module in installed_modules(modules, False):
        m, _, p = module
        if not enabled(m):
            continue

        try:
            import_module(f"modules.{p}.forms")
        except ModuleNotFoundError:
            pass


def login_form(priority: int = 1) -> Callable:
    check_priority(priority)

    def decorator(cls):
        if not priority in _login_forms:
            _login_forms[priority] = []
        _login_forms[priority].append(cls)
        return cls

    return decorator


def register_form(priority: int = 1) -> Callable:
    check_priority(priority)

    def decorator(cls):
        if not priority in _register_forms:
            _register_forms[priority] = []
        _register_forms[priority].append(cls)
        return cls

    return decorator


def build_login_form() -> type:
    bases = tuple()
    for configs in build_sorted_tuple(_login_forms):
        bases += tuple(configs)

    return type(
        "ExtendedLoginForm",
        bases + (LoginForm, ),
        {}
    )


def build_register_form() -> type:
    bases = tuple()
    for configs in build_sorted_tuple(_register_forms):
        bases += tuple(configs)

    return type(
        "ExtendedRegisterForm",
        bases + (RegisterFormV2, ),
        {}
    )


def send_security_mail(msg: dict):
    message = EmailMessage(
        subject=msg["subject"],
        body=msg["body"],
        from_email=msg["sender"],
        to=[msg["recipient"]],
    )
    Thread(target=message.send).start()
