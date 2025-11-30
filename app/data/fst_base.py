from flask_security.models import fsqla_v3 as fsqla

from ..extensions import db

user_roles = db.Table(
    "user_roles",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("role_id", db.Integer, db.ForeignKey("role.id"), primary_key=True)
)

fsqla.FsModels.set_db_info(db)


class User(db.Model, fsqla.FsUserMixin):
    pass


class Role(db.Model, fsqla.FsRoleMixin):
    pass
