from pathlib import Path
from importlib import import_module

_package = Path(__file__).parent


def init_models():
    for file in _package.rglob("*.py"):
        if file.stem == "__init__":
            continue
        import_module(f"flaskpp.app.data.{file.stem}")


def commit():
    from ..extensions import db
    db.session.commit()


def add_model(model, auto_commit: bool = True):
    from ..extensions import db
    db.session.add(model)
    if auto_commit:
        commit()


def delete_model(model, auto_commit: bool = True):
    from ..extensions import db
    db.session.delete(model)
    if auto_commit:
        commit()
