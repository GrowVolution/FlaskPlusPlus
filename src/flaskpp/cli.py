from pathlib import Path
import typer, os, subprocess, sys

from .modules.cli import modules_entry
from .utils.setup import setup
from .utils.run import run
from .utils.service_registry import registry_entry

app = typer.Typer(help="Flask++ CLI")
cli_home = Path(__file__).parent


@app.command()
def init():
    typer.echo(typer.style("Creating default structure...", bold=True))

    root = Path(os.getcwd())
    (root / "templates").mkdir(exist_ok=True)
    translations = root / "translations"
    translations.mkdir(exist_ok=True)
    static = root / "static"
    static.mkdir(exist_ok=True)
    (static / "css").mkdir(exist_ok=True)
    (static / "js").mkdir(exist_ok=True)
    (static / "img").mkdir(exist_ok=True)
    with open(root / "main.py", "w") as f:
        f.write("""
from flaskpp import FlaskPP
            
def create_app(config_name: str = "default"):
    app = FlaskPP(__name__, config_name)
    # TODO: Extend the Flask++ default setup with your own factory
    return app

app = create_app().to_asgi()
        """)

    typer.echo(typer.style("Generation default translations...", bold=True))

    pot = "messages.pot"
    trans = "translations"
    babel_cli = "babel.messages.frontend"
    has_catalogs = any(translations.glob("*/LC_MESSAGES/*.po"))

    subprocess.run([
        sys.executable, "-m", babel_cli, "extract",
        "-F", str(cli_home / "babel.cfg"),
        "-o", pot,
        ".", str(cli_home.resolve())
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

    typer.echo(typer.style("Flask++ project successfully initialized.", fg=typer.colors.GREEN, bold=True))

app.command()(setup)
app.command()(run)


def main():
    modules_entry(app)
    registry_entry(app)
    app()


if __name__ == "__main__":
    main()
