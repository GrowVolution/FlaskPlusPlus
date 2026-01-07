from git import Repo, exc
from pathlib import Path
import typer, shutil, json

from flaskpp.flaskpp import version
from flaskpp.module import version_check
from flaskpp.modules import module_home, creator_templates
from flaskpp.utils import prompt_yes_no, sanitize_text, safe_string

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
    if not src:
        raise NotImplementedError("Module hub is not ready yet.")

    typer.echo(f"Installing {module_id}...")
    mod_src = Path(src)
    mod_dst = module_home / module_id
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


@modules.command()
def create(
        module: str
):
    tmp_id = safe_string(module).lower()
    mod_id = sanitize_text(input(f"Enter your module id ({tmp_id}): "))
    if not mod_id.strip():
        mod_id = tmp_id
    else:
        mod_id = safe_string(mod_id)

    module_dst = module_home / mod_id
    if module_dst.exists():
        typer.echo(typer.style(
            f"There is already a folder named '{mod_id}' in modules.",
            fg=typer.colors.YELLOW, bold=True
        ))
        if not prompt_yes_no("Do you want to overwrite it? (y/N)"):
            return
        shutil.rmtree(module_dst)
    module_dst.mkdir(exist_ok=True)

    manifest = {
        "id": mod_id,
        "name": sanitize_text(input(f"Enter the name of your module ({module}): ")),
        "description": sanitize_text(input("Describe your module briefly: ")),
        "version": sanitize_text(input("Enter the version of your module [required]: ")),
        "author": sanitize_text(input("Enter your name or nickname: ")),
        "requires": {
            "fpp": f">={str(version()).strip("v")}",
            "modules": {}
        }
    }
    if not manifest["name"].strip():
        manifest["name"] = module

    check = version_check(manifest["version"])
    while not check[0]:
        typer.echo(typer.style(check[1], fg=typer.colors.RED, bold=True))
        manifest["version"] = sanitize_text(input("Enter a correct version string: "))
        check = version_check(manifest["version"])

    for info in ["description", "author"]:
        if not manifest[info].strip():
            typer.echo(typer.style(f"Missing {info}... Ignoring manifest entry.", fg=typer.colors.YELLOW, bold=True))
            manifest.pop(info)

    typer.echo(typer.style(f"Writing manifest...", bold=True))
    (module_dst / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False)
    )

    typer.echo(typer.style(f"Creating basic structure...", bold=True))
    (module_dst / "handling").mkdir(exist_ok=True)

    static = module_dst / "static"
    static.mkdir(exist_ok=True)
    css = static / "css"
    css.mkdir(exist_ok=True)
    (static / "js").mkdir(exist_ok=True)
    (static / "img").mkdir(exist_ok=True)

    templates = module_dst / "templates"
    templates.mkdir(exist_ok=True)

    (module_dst / "routes.py").write_text(creator_templates.module_routes)
    (templates / f"index.html").write_text(creator_templates.module_index)
    (templates / f"vite_index.html").write_text(creator_templates.module_vite_index)
    (css / "tailwind_raw.css").write_text(creator_templates.tailwind_raw)

    typer.echo(typer.style(f"Setting up requirements...", bold=True))

    required = []
    for extension in creator_templates.extensions:
        require = prompt_yes_no(f"Do you want to use {extension} in this module? (y/N) ")
        if not require:
            continue
        required.append(f'"{extension}"')
        if extension == "sqlalchemy":
            data = module_dst / "data"
            data.mkdir(exist_ok=True)
            (data / "__init__.py").write_text(creator_templates.module_data_init)

    (module_dst / "__init__.py").write_text(
        creator_templates.module_init.format(
            requirements=",\n\t\t".join(required)
        )
    )

    typer.echo(typer.style(
        f"Module '{module}' has been successfully created.",
        fg=typer.colors.GREEN, bold=True
    ))


def modules_entry(app: typer.Typer):
    app.add_typer(modules, name="modules")
