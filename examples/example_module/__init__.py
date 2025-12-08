from flask import Blueprint
from pathlib import Path

from flaskpp import FlaskPP
from flaskpp.modules import require_extensions
from .data import init_models

NAME = __name__
bp = Blueprint(NAME, NAME, template_folder="templates", static_folder="static")


@bp.context_processor
def context_processor():
    return dict(
        NAME=NAME
    )


@require_extensions("sqlalchemy")
def register_module(app: FlaskPP, home: bool):
    if home:
        bp.static_url_path = f"/{NAME}/static"
    else:
        bp.url_prefix = f"/{NAME}"

    from .routes import init_routes
    init_routes(bp)

    app.register_blueprint(bp)
    init_models()
