import json, typer, shutil

from flaskpp.flaskpp import version
from flaskpp.module import version_check
from flaskpp.modules import creator_templates, module_home, _setup_globals
from flaskpp.utils import prompt_yes_no, sanitize_text, safe_string


def create_module(module_name: str):
    _setup_globals()

    tmp_id = safe_string(module_name).lower()
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
        "name": sanitize_text(input(f"Enter the name of your module ({module_name}): ")),
        "description": sanitize_text(input("Describe your module briefly: ")),
        "version": sanitize_text(input("Enter the version of your module [required]: ")),
        "author": sanitize_text(input("Enter your name or nickname: ")),
        "requires": {
            "fpp": f">={str(version()).strip("v")}",
            "packages": [],
            "modules": {}
        }
    }
    if not manifest["name"].strip():
        manifest["name"] = module_name

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
    handling = module_dst / "handling"
    handling.mkdir(exist_ok=True)
    (handling / "__init__.py").write_text(
        creator_templates.module_handling
    )
    (handling / "vite_index.py").write_text(
        creator_templates.handling_example
    )

    static = module_dst / "static"
    static.mkdir(exist_ok=True)
    css = static / "css"
    css.mkdir(exist_ok=True)
    (static / "js").mkdir(exist_ok=True)
    (static / "img").mkdir(exist_ok=True)

    templates = module_dst / "templates"
    templates.mkdir(exist_ok=True)


    config_name = ""
    for s in mod_id.split("_"):
        config_name += s.capitalize()

    (module_dst / "config.py").write_text(
        creator_templates.module_config.format(
            name=config_name
    ))
    (module_dst / "routes.py").write_text(
        creator_templates.module_routes
    )
    (templates / f"index.html").write_text(
        creator_templates.module_index
    )
    (templates / f"vite_index.html").write_text(
        creator_templates.module_vite_index
    )
    (css / "tailwind_raw.css").write_text(creator_templates.tailwind_raw)

    extract = module_dst / "extract"
    (extract / "static").mkdir(parents=True, exist_ok=True)
    (extract / "templates").mkdir(exist_ok=True)

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
        f"Module '{module_name}' has been successfully created.",
        fg=typer.colors.GREEN, bold=True
    ))
