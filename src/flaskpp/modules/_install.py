from pathlib import Path
from git import Repo, exc
import typer, shutil

from flaskpp.modules import module_home

def install_module(module_id: str, src: str):
    if not src:
        raise NotImplementedError("Module hub is not ready yet.")

    typer.echo(f"Installing {module_id}...")
    mod_src = Path(src)
    mod_dst = module_home / module_id
    if mod_src.exists():
        typer.echo(typer.style(
            "Loading module from local path...",  bold=True
        ))
        if mod_src.parent.resolve() == module_home.resolve():
            typer.echo(typer.style(
                "Module already installed.",
                fg=typer.colors.YELLOW, bold=True
            ))
            return
        shutil.copytree(mod_src, mod_dst, dirs_exist_ok=True)
        return

    if not src.startswith("http"):
        raise ValueError("Invalid source format.")

    try:
        typer.echo(typer.style(
            "Loading module from remote repository...",  bold=True
        ))
        Repo.clone_from(src, mod_dst)
    except exc.GitCommandError:
        typer.echo(typer.style(
            "Failed to clone from source.",
            fg=typer.colors.YELLOW, bold=True
        ))

    typer.echo(typer.style(
        f"Module '{module_id}' has been successfully installed.",
        fg=typer.colors.GREEN, bold=True
    ))
