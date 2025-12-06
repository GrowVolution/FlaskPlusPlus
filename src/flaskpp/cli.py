from pathlib import Path
import typer, os, subprocess, sys

from .modules.cli import register as module_cli
from .utils.setup import setup
from .utils.run import run

app = typer.Typer()
cli_home = Path(__file__).parent


@app.command()
def init():
    typer.echo(typer.style("Creating default structure...", bold=True))

    root = Path(os.getcwd())
    (root / "templates").mkdir(exist_ok=True)
    static = root / "static"
    static.mkdir(exist_ok=True)
    (static / "css").mkdir(exist_ok=True)
    (static / "js").mkdir(exist_ok=True)
    (static / "img").mkdir(exist_ok=True)
    with open(root / "main.py", "w") as f:
        f.write("""
            from flaskpp import FlaskPP
            
            def create_app(config_name: str = "default"):
            \tapp = FlaskPP(__name__, config_name)
            \t# TODO: Extend the Flask++ default setup with your own factory
            \treturn app
            
            app = create_app().to_asgi()
        """)

    typer.echo(typer.style("Generation default translations...", bold=True))

    pot = "messages.pot"
    trans = "translations"
    subprocess.run([
        sys.executable, "-m", "pybabel", "extract",
        "-F", str(cli_home / "babel.cfg"),
        "-o", pot,
        ".", str(cli_home.resolve())
    ])

    subprocess.run([
        sys.executable, "-m", "pybabel", "update",
        "-i", pot,
        "-d", trans
    ])

    subprocess.run([
        sys.executable, "-m", "pybabel", "init",
        "-i", pot,
        "-d", trans,
        "-l", "en"
    ])

    subprocess.run([
        sys.executable, "-m", "pybabel", "compile",
        "-d", trans
    ])

app.command()(setup)
app.command()(run)


def main():
    module_cli(app)
    app()


if __name__ == "__main__":
    main()
