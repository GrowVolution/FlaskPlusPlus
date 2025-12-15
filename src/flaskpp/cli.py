from pathlib import Path
from importlib.metadata import version
import typer, os, subprocess, sys

from flaskpp.modules.cli import modules_entry
from flaskpp.utils.setup import setup
from flaskpp.utils.run import run
from flaskpp.utils.service_registry import registry_entry
from flaskpp.tailwind import setup_tailwind
from flaskpp.fpp_node import load_node
from flaskpp.fpp_node.vite import prepare_vite
from flaskpp.fpp_node.cli import node_entry

app = typer.Typer(help="Flask++ CLI")
cli_home = Path(__file__).parent


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    version_flag: bool = typer.Option(
        False, "--version", "-v",
        help="Show the current version of Flask++.",
        is_eager=True
    ),
    help_flag: bool = typer.Option(
        False, "--help", "-h",
        help="Get help about all commands.",
        is_eager=True
    )
):
    if version_flag:
        typer.echo(f"Flask++ v{version('flaskpp')}")
        raise typer.Exit()

    if help_flag:
        typer.echo(
            "Usage: \n\t" + typer.style("fpp [args]", bold=True) + "\n"
            "\t" + typer.style("fpp [command] [args]", bold=True) + "\n"
            "\t" + typer.style("fpp [subcli] [command] [args]", bold=True) + "\n\n"
            "Arguments:\n\t-v, --version\t   - Show the current version of Flask++.\n"
            "\t-h, --help\t   - Show this help message.\n\n"
            "Commands:\n\tinit\t\t   - Creates the Flask++ basic structure in the current working directory.\n"
            "\tsetup\t\t   - Starts the Flask++ app setup tool. (Can be run multiple times.)\n"
            "\trun\t\t   - The Flask++ native app control. (Using uvicorn.)\n\n"
            "Sub-CLIs:\n\tmodules\t\t   - Manages the modules of Flask++ apps.\n"
            "\tregistry\t   - Manages the app service registry for you. (Requires admin privileges.)\n"
            "\tnode\t\t   - Allows you to run node commands with the standalone node cli. (" + typer.style("fpp node [npm/npx] [args]", bold=True) + ")\n\n" +
            typer.style("fpp run [args]", bold=True) + "\n"
            "\t-i, --interactive  - Starts all your apps in interactive mode and lets you manage them.\n"
            "\t-a, --app\t   - Specify the name of a specific app, if you don't want to run interactive.\n"
            "\t-p, --port\t   - Specify the port on which your app should listen. (Default is 5000.)\n"
            "\t-d, --debug\t   - Run your app in debug mode, to get more detailed tracebacks and log debug messages. (Default is False.)\n"
            "\t\t\t   " + typer.style("If FRONTEND_ENGINE is enabled, vite will run in dev mode. Every module runs its own dev server.", fg=typer.colors.MAGENTA) + "\n\n\n" +
            typer.style("fpp modules [command] [args]", bold=True) + "\n"
            "\tinstall\t\t   - Install a specified Flask++ module.\n"
            "\tcreate\t\t   - Automatically create a new module to make things easier.\n\n" +
            typer.style("fpp modules install [name] [args]", bold=True) + "\n"
            "\tname\t\t   - The name of the module to install.\n"
            "\t-s, --src\t   - Specify the name of a source directory or git remote repository to install.\n"
            "\t" + typer.style(
                "If you install from a source, name will be the installed name.\n"
                "\tIf you only specify the name, the module will be installed from our hub. (Coming soon.)",
                fg=typer.colors.MAGENTA
            ) + "\n\n" +
            typer.style("fpp modules create [name]", bold=True) + "\n"
            "\tname\t\t   - The name of the module you want to create.\n\n\n" +
            typer.style("fpp registry [command] [args]", bold=True) + "\n"
            "\tregister\t   - Register an app as a system service. (Executed when system boots up.)\n"
            "\tremove\t\t   - Remove your app from system services.\n"
            "\tstart\t\t   - Start your apps system service.\n"
            "\tstop\t\t   - Stop your apps system service.\n\n" +
            typer.style("fpp registry register [args]", bold=True) + "\n"
            "\t-a, --app\t   - The name of your app, which you want to register as a service.\n"
            "\t-p, --port\t   - The port on which your apps service should run. (Default is 5000.)\n"
            "\t-d, --debug\t   - If your service should run in debug mode.\n\n" +
            typer.style("fpp registry [remove/start/stop] [name]", bold=True) + "\n"
            "\tname\t\t   - The name of the app (which - of course - also is the service name)."
        )
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        typer.echo("For further information use: " + typer.style("fpp --help", bold=True))
        raise typer.Exit()


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

    setup_tailwind()

    load_node()
    prepare_vite()

    typer.echo(typer.style("Flask++ project successfully initialized.", fg=typer.colors.GREEN, bold=True))

app.command()(setup)
app.command()(run)


def main():
    modules_entry(app)
    registry_entry(app)
    node_entry(app)
    app()


if __name__ == "__main__":
    main()
