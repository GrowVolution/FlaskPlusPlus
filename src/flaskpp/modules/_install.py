from pathlib import Path
from git import Repo, exc
from importlib import import_module
import typer, shutil

from flaskpp.modules import setup_globals

def install_module(module_id: str, src: str):
    module_home, _ = setup_globals()

    if not src:
        raise NotImplementedError("Module hub is not ready yet.")

    def finalize():
        try:
            mod = import_module(f"modules.{module_id}")
            module = getattr(mod, "module", None)

            from flaskpp import Module
            if not isinstance(module, Module):
                raise ImportError("Failed to import 'module: Module'.")

            module.extract()
            module.install_packages()

            typer.echo(typer.style(
                f"Module '{module}' has been successfully installed.",
                fg=typer.colors.GREEN, bold=True
            ))

        except (ModuleNotFoundError, ImportError, TypeError) as e:
            typer.echo(typer.style(
                f"Failed to load module: {e}",
                fg=typer.colors.RED, bold=True
            ))

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
        finalize()
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
        return

    finalize()
