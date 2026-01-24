from flask_security.models import fsqla_v3 as fsqla
from typing import Callable
import inspect

from flaskpp.utils import check_priority, build_sorted_tuple
from flaskpp.app.extensions import db

_user_mixins: dict[int, list[type]] = {}
_role_mixins: dict[int, list[type]] = {}


def _valid_mixin(cls: type, kind: str):
    if not inspect.isclass(cls):
        raise TypeError(f"{kind} mixin must be a class.")
    if hasattr(cls, "__tablename__"):
        raise TypeError(f"{kind} mixins must not define tables.")


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


def _build_user_model() -> type:
    return type(
        "User",
        build_sorted_tuple(_user_mixins, (db.Model, fsqla.FsUserMixin)),
        {}
    )


def _build_role_model() -> type:
    return type(
        "Role",
        build_sorted_tuple(_role_mixins, (db.Model, fsqla.FsRoleMixin)),
        {}
    )


user_roles = db.Table(
    "user_roles",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("role_id", db.Integer, db.ForeignKey("role.id"), primary_key=True)
)

fsqla.FsModels.set_db_info(db)


User = _build_user_model()
Role = _build_role_model()
