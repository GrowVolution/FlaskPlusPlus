
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
from flaskpp import Module

module = Module(
    __file__,
    __name__,
    [
        {requirements}
    ]
)

"""

module_routes = """
from flaskpp import Module


def init_routes(mod: Module):
    @mod.route("/")
    def index():
        return mod.render_template("index.html")

"""

module_index = """
{% extends "base_example.html" %}
{# The base template is natively provided by Flask++. #}

{% block title %}{{ _('My Module') }}{% endblock %}
{% block content %}
    <div class="wrapped-center">
        <h2>{{ _('Welcome!') }}</h2>
        <p>{{ _('This is my wonderful new module.') }}</p>
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

module_manifest = """
{{
  "name": "{name}",
  "description": "{description}",
  "version": "{version}",
  "author": "{author}"
}}
"""
