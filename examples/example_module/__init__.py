from flask import Blueprint, Flask
from pathlib import Path

from flaskpp.modules import require_extensions
from .data import init_models

NAME = Path(__file__).parent.name
bp = Blueprint(NAME, __name__, template_folder="templates", static_folder="static")


@bp.context_processor
def context_processor():
    return dict(
        NAME=NAME
    )


@require_extensions("sqlalchemy")
def register_module(app: Flask, home: bool):
    if home:
        bp.static_url_path = f"/{NAME}/static"
    else:
        bp.url_prefix = f"/{NAME}"

    from .routes import init_routes
    init_routes(bp)

    app.register_blueprint(bp)
    init_models()
