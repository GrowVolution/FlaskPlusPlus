import typer

from flaskpp.modules._install import install_module
from flaskpp.modules._create import create_module

modules = typer.Typer(help="Manage the modules of Flask++ apps.")


@modules.command()
def install(
        module_id: str,
        src: str = typer.Option(
            None,
            "-s", "--src",
            help="Optional source for your module",
        )
):
    install_module(module_id, src)


@modules.command()
def create(module: str):
    create_module(module)


def modules_entry(app: typer.Typer):
    app.add_typer(modules, name="modules")
