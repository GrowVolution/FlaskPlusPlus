from flask_security.models import fsqla_v3 as fsqla
from importlib import import_module
from pathlib import Path
from typing import Callable, TYPE_CHECKING
import inspect

from flaskpp.utils import check_priority, build_sorted_tuple, enabled
from flaskpp.app.extensions import db

if TYPE_CHECKING:
    from flaskpp import FlaskPP

_user_mixins: dict[int, list[type]] = {}
_role_mixins: dict[int, list[type]] = {}


def _valid_mixin(cls: type, kind: str):
    if not inspect.isclass(cls):
        raise TypeError(f"{kind} mixin must be a class.")
    if hasattr(cls, "__tablename__"):
        raise TypeError(f"{kind} mixins must not define tables.")


def init_mixins(app: "FlaskPP"):
    modules = Path(app.root_path) / "modules"

    if not modules.exists() or not modules.is_dir():
        return

    for module in modules.iterdir():
        if not module.is_dir():
            continue

        fst_data = module / "data" / "noinit_fst.py"
        if fst_data.exists():
            import_module(f"modules.{module.name}.data.noinit_fst")


def user_mixin(priority: int = 1) -> Callable:
    check_priority(priority)

    def decorator(cls):
        _valid_mixin(cls, "User")
        if priority not in _user_mixins:
            _user_mixins[priority] = []
        _user_mixins[priority].append(cls)
        return cls
    return decorator


def role_mixin(priority: int = 1) -> Callable:
    check_priority(priority)

    def decorator(cls):
        _valid_mixin(cls, "Role")
        if priority not in _role_mixins:
            _role_mixins[priority] = []
        _role_mixins[priority].append(cls)
        return cls
    return decorator


def build_user_model() -> type:
    bases = tuple()
    for mixins in build_sorted_tuple(_user_mixins):
        bases += tuple(mixins)

    return type(
        "User",
        bases + (db.Model, fsqla.FsUserMixin),
        {}
    )


def build_role_model() -> type:
    bases = tuple()
    for mixins in build_sorted_tuple(_role_mixins):
        bases += tuple(mixins)

    return type(
        "Role",
        bases + (db.Model, fsqla.FsRoleMixinV2),
        {}
    )

if enabled("EXT_FST"):
    fsqla.FsModels.set_db_info(db)
