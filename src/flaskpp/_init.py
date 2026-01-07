from pathlib import Path
import typer, subprocess, sys, os

from flaskpp import _fpp_root
from flaskpp.tailwind import setup_tailwind
from flaskpp.fpp_node import load_node
from flaskpp.fpp_node.fpp_vite import prepare_vite


def initialize(skip_defaults: bool, skip_babel: bool, skip_tailwind: bool, skip_node: bool, skip_vite: bool):
    typer.echo(typer.style("Creating default structure...", bold=True))

    root = Path.cwd()

    if not skip_defaults:
        from flaskpp.utils.setup import conf_path
        conf_path.mkdir(exist_ok=True)

        from flaskpp.modules import module_home
        module_home.mkdir(exist_ok=True)

        from flaskpp.utils.service_registry import service_path
        service_path.mkdir(exist_ok=True)


        templates = root / "templates"
        templates.mkdir(exist_ok=True)
        static = root / "static"
        static.mkdir(exist_ok=True)
        css = static / "css"
        css.mkdir(exist_ok=True)
        (static / "js").mkdir(exist_ok=True)
        (static / "img").mkdir(exist_ok=True)
        with open(root / "main.py", "w") as f:
            f.write("""
from flaskpp import FlaskPP
            
def create_app(config_name: str = "default"):
    app = FlaskPP(__name__, config_name)

    # TODO: Extend the Flask++ default setup with your own factory

    return app

if __name__ == "__main__":
    app = create_app()
    app.start()
            """)

        (templates / "index.html").write_text("""
{% extends "base_example.html" %}
{# The base template is natively provided by Flask++. #}

{% block title %}{{ _('Home') }}{% endblock %}
{% block content %}
    <div class="text-center">
        <h2>{{ _('My new Flask++ Project') }}</h2>
        <p>
            {{ _('This is my brand new, super cool project.') }}
            
        </p>
    </div>
{% endblock %}
        """)

        (css / "tailwind_raw.css").write_text("""
@import "tailwindcss" source("../../");

@source not "../../.venv";
@source not "../../venv";

@source not "../../vite";
@source not "../../modules";

@theme {
    /* ... */
}
        """)

    if not skip_babel:
        typer.echo(typer.style("Generating default translations...", bold=True))

        translations = root / "translations"
        translations.mkdir(exist_ok=True)

        pot = "messages.pot"
        trans = "translations"
        babel_cli = "babel.messages.frontend"
        has_catalogs = any(translations.glob("*/LC_MESSAGES/*.po"))

        subprocess.run([
            sys.executable, "-m", babel_cli, "extract",
            "-F", str(_fpp_root / "babel.cfg"),
            "-o", pot,
            os.getcwd(), str(_fpp_root.resolve())
        ])

        if has_catalogs:
            subprocess.run([
                sys.executable, "-m", babel_cli, "update",
                "-i", pot,
                "-d", trans
            ])

        else:
            subprocess.run([
                sys.executable, "-m", babel_cli, "init",
                "-i", pot,
                "-d", trans,
                "-l", "en"
            ])

        subprocess.run([
            sys.executable, "-m", babel_cli, "compile",
            "-d", trans
        ])

    if not skip_tailwind: setup_tailwind()

    if not skip_node: load_node()
    if not skip_vite: prepare_vite()

    typer.echo(typer.style("Flask++ project successfully initialized.", fg=typer.colors.GREEN, bold=True))
