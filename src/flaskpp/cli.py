from importlib.metadata import version
import typer

from flaskpp._help import help_message
from flaskpp._init import initialize
from flaskpp.modules.cli import modules_entry
from flaskpp.utils.setup import setup_entry
from flaskpp.utils.run import run_entry
from flaskpp.utils.service_registry import registry_entry
from flaskpp.fpp_node.cli import node_entry
from flaskpp.tailwind.cli import tailwind_entry

app = typer.Typer(help="Flask++ CLI")


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
        help_message()
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        typer.echo("For further information use: " + typer.style("fpp --help", bold=True))
        raise typer.Exit()


@app.command()
def init(
    skip_defaults: bool = typer.Option(False, "--skip-defaults"),
    skip_babel: bool = typer.Option(False, "--skip-babel"),
    skip_tailwind: bool = typer.Option(False, "--skip-tailwind"),
    skip_node: bool = typer.Option(False, "--skip-node"),
    skip_vite: bool = typer.Option(False, "--skip-vite"),
):
    initialize(skip_defaults, skip_babel, skip_tailwind, skip_node, skip_vite)


def main():
    setup_entry(app)
    run_entry(app)

    modules_entry(app)
    registry_entry(app)

    node_entry(app)
    tailwind_entry(app)

    app()


if __name__ == "__main__":
    main()
