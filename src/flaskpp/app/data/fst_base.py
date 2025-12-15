from flask_security.models import fsqla_v3 as fsqla
import inspect

from flaskpp.app.extensions import db

_user_mixins: list[type] = []
_role_mixins: list[type] = []


def _valid_mixin(cls, kind: str):
    if not inspect.isclass(cls):
        raise TypeError(f"{kind} mixin must be a class.")
    if hasattr(cls, "__tablename__"):
        raise TypeError(f"{kind} mixins must not define tables.")


def user_mixin(cls):
    _valid_mixin(cls, "User")
    _user_mixins.append(cls)
    return cls


def role_mixin(cls):
    _valid_mixin(cls, "Role")
    _role_mixins.append(cls)
    return cls


def _build_user_model():
    bases = tuple(_user_mixins) + (db.Model, fsqla.FsUserMixin)

    return type(
        "User",
        bases,
        {}
    )


def _build_role_model():
    bases = tuple(_role_mixins) + (db.Model, fsqla.FsRoleMixin)

    return type(
        "Role",
        bases,
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
