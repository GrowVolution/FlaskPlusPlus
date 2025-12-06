from git import Repo, exc
from pathlib import Path
import typer, shutil

from ..modules import module_home


def register(app):

    @app.command()
    def install(
        module: str,
        src: str = typer.Option(
            None,
            "-s", "--src",
            help="Optional source for your module",
        )
    ):
        if not src:
            raise NotImplementedError("Module hub is not ready yet.")

        typer.echo(f"Installing {module}...")
        mod_src = Path(src)
        mod_dst = module_home / module
        if mod_src.exists():
            typer.echo(f"Loading module from local path...")
            if mod_src.parent.resolve() == module_home.resolve():
                typer.echo("Module already installed.")
                return
            shutil.copytree(mod_src, mod_dst, dirs_exist_ok=True)
            return

        if not src.startswith("http"):
            raise ValueError("Invalid source format.")

        try:
            typer.echo(f"Loading module from remote repository...")
            Repo.clone_from(src, mod_dst)
        except exc.GitCommandError:
            typer.echo("Failed to clone from source.")
