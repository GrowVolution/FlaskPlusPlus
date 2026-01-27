from pathlib import Path
from importlib import import_module
from flask_security.forms import LoginForm, RegisterFormV2
from typing import Callable, TYPE_CHECKING

from flaskpp.modules import installed_modules
from flaskpp.utils import check_priority, build_sorted_tuple, enabled

if TYPE_CHECKING:
    from flaskpp import FlaskPP

_login_forms: dict[int, list[type]] = {}
_register_forms: dict[int, list[type]] = {}


class FormMeta(type): pass


def init_forms(app: "FlaskPP"):
    modules = Path(app.root_path) / "modules"

    if not modules.exists() or not modules.is_dir():
        return

    for module in installed_modules(modules, False):
        m, _, p = module
        if not enabled(m):
            continue

        try:
            import_module(f"modules.{p}.config")
        except ModuleNotFoundError:
            pass


def login_form(priority: int = 1) -> Callable:
    check_priority(priority)

    def decorator(cls):
        if not priority in _login_forms:
            _login_forms[priority] = []

        if not isinstance(type(cls), FormMeta):
            cls = FormMeta(cls.__name__, cls.__bases__, dict(cls.__dict__))

        _login_forms[priority].append(cls)
        return cls

    return decorator


def register_form(priority: int = 1) -> Callable:
    check_priority(priority)

    def decorator(cls):
        if not priority in _register_forms:
            _register_forms[priority] = []

        if not isinstance(type(cls), FormMeta):
            cls = FormMeta(cls.__name__, cls.__bases__, dict(cls.__dict__))

        _register_forms[priority].append(cls)
        return cls

    return decorator


def build_login_form() -> FormMeta:
    cls = LoginForm
    default_conf = FormMeta(cls.__name__, cls.__bases__, dict(cls.__dict__))

    bases = tuple()
    for configs in build_sorted_tuple(_login_forms):
        bases += tuple(configs)

    return FormMeta(
        "ExtendedLoginForm",
        bases + (default_conf, ),
        {}
    )


def build_register_form() -> FormMeta:
    cls = RegisterFormV2
    default_conf = FormMeta(cls.__name__, cls.__bases__, dict(cls.__dict__))

    bases = tuple()
    for configs in build_sorted_tuple(_register_forms):
        bases += tuple(configs)

    return FormMeta(
        "ExtendedRegisterForm",
        bases + (default_conf, ),
        {}
    )
