from pathlib import Path
from importlib import import_module
from datetime import datetime
from typing import TYPE_CHECKING
import os

from flaskpp.utils.debugger import log

if TYPE_CHECKING:
    from flask import Flask
    from flaskpp import FlaskPP
    from flaskpp.app.extensions import db

_package = Path(__file__).parent


def init_models():
    for file in _package.rglob("*.py"):
        if file.stem == "__init__" or file.stem.startswith("noinit"):
            continue
        import_module(f"flaskpp.app.data.{file.stem}")


def commit():
    from ..extensions import db
    db.session.commit()


def add_model(model: "db.Model", auto_commit: bool = True):
    from ..extensions import db
    db.session.add(model)
    if auto_commit:
        commit()


def delete_model(model: "db.Model", auto_commit: bool = True):
    from ..extensions import db
    db.session.delete(model)
    if auto_commit:
        commit()


def db_autoupdate(app: "FlaskPP | Flask"):
    message = f"App-Factory autoupdate - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    with app.app_context():
        from flask_migrate import init as fm_init, migrate as fm_migrate, upgrade as fm_upgrade
        migrations = os.path.join(app.root_path, "migrations")
        if not os.path.isdir(migrations):
            fm_init(directory=migrations)
        fm_migrate(message=message, directory=migrations)

        _fix_missing(migrations)
        fm_upgrade(directory=migrations)


def _fix_missing(migrations: str):
    versions_path = os.path.join(migrations, "versions")
    if os.path.isdir(versions_path):
        files = sorted(
            [f for f in os.listdir(versions_path) if f.endswith(".py")],
            key=lambda x: os.path.getmtime(os.path.join(versions_path, x)),
        )
        if files:
            latest_file = os.path.join(versions_path, files[-1])
            with open(latest_file, "r", encoding="utf-8") as f:
                content = f.read()

            import_str = f"import flask_security"
            if "flask_security" in content and import_str not in content:
                content = f"{import_str}\n{content}"
                with open(latest_file, "w", encoding="utf-8") as f:
                    f.write(content)
                log("migrate", f"Fixed missing flask_security import in {latest_file}")
