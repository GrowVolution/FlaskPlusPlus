
extensions = [
    "sqlalchemy",
    "socket",
    "babel",
    "fst",
    "authlib",
    "mailing",
    "cache",
    "api",
    "jwt_extended"
]

module_init = """
from flask import Blueprint
from pathlib import Path

from flaskpp import FlaskPP

from .data import init_models

NAME = __name__
bp = Blueprint(NAME, NAME, template_folder="templates", static_folder="static")


@bp.context_processor
def context_processor():
    return dict(
        NAME=NAME
    )

{ requirements }
def register_module(app: FlaskPP, home: bool):
    if home:
        bp.static_url_path = f"/{NAME}/static"
    else:
        bp.url_prefix = f"/{NAME}"

    from .routes import init_routes
    init_routes(bp)

    app.register_blueprint(bp)
    init_models()

"""

module_requirements = """
from flaskpp.modules import require_extensions
@require_extensions(
    { extensions }
)
"""

module_routes = """
from flask import Blueprint

from .utils import render_template


def init_routes(bp: Blueprint):
    @bp.route("/")
    def index():
        return render_template("index.html")

"""

module_utils = """
from flask import render_template as _render_template

from . import NAME


def render_template(template: str, **context) -> str:
    return _render_template(f"{NAME}/{template}", **context)

"""

module_index = """
{% extends "base_example.html" %}
{# The base template is natively provided by Flask++. #}

{% block title %}{{ _('Home') }}{% endblock %}
{% block content %}
    <div class="wrapped-center">
        <h2>{{ _('Welcome!') }}</h2>
        <p>{{ _('This is your wonderful new app.') }}</p>
        <img src="{{ url_for(NAME ~ '.static', filename='picture.jpg') }}" alt="{{ _('Picture') }}"
             class="img-fluid rounded mx-auto d-block">
    </div>
{% endblock %}
"""

module_data_init = """
from pathlib import Path
from importlib import import_module

_package = Path(__file__).parent


def init_models():
    from .. import NAME
    for file in _package.rglob("*.py"):
        if file.stem == "__init__":
            continue
        import_module(f"modules.{NAME}.data.{file.stem}")

"""
