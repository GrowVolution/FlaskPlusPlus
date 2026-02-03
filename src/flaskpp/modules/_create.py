import json, typer, shutil

from flaskpp.flaskpp import version
from flaskpp.module import version_check
from flaskpp.modules import creator_templates, setup_globals, import_base
from flaskpp.utils import prompt_yes_no, sanitize_text, safe_string


def _config_name(mod_id: str) -> str:
    config_name = ""
    for s in mod_id.split("_"):
        config_name += s.capitalize()
    return config_name


def create_module(module_name: str):
    module_home, _ = setup_globals()

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
        if not prompt_yes_no("Do you want to overwrite it? (y/N) "):
            return
        shutil.rmtree(module_dst)
    module_dst.mkdir(exist_ok=True)

    base_module = prompt_yes_no("Do you want to create a base module? (y/N) ")
    extends = False if base_module else prompt_yes_no("Do you want to extend another module? (y/N) ")

    extend_import = ""
    extend_id = ""
    extend = ""
    base = None
    if extends:
        extend_import = f"from flaskpp.modules import import_base\n"

        extend_id = sanitize_text(input("Enter the id of the module you want to extend [required]: "))
        while not extend_id.strip():
            typer.echo(typer.style(
                "If you want to extend another module, you must provide its id.",
                fg=typer.colors.RED, bold=True
            ))
            extend_id = sanitize_text(input("Enter a module id: "))

        new_extend_id = safe_string(extend_id)
        if new_extend_id != extend_id:
            typer.echo(typer.style(
                f"Module ids must be safe strings! Changed '{extend_id}' to '{new_extend_id}'.",
                fg=typer.colors.YELLOW
            ))

        extend_id = new_extend_id
        base = import_base(extend_id)
        if not base:
            typer.echo(typer.style(
                f"There is no module with id '{extend_id}' installed inside this project.",
                fg=typer.colors.RED, bold=True
            ))
            if not prompt_yes_no("Do you want to continue anyway? (y/N)"):
                return

        extend = f'import_base("{extend_id}")'

    manifest = {
        "id": mod_id,
        "name": sanitize_text(input(f"Enter the name of your module ({module_name}): ")),
        "description": sanitize_text(input("Describe your module briefly: ")),
        "version": sanitize_text(input("Enter the version of your module [required]: ")),
        "type": "base" if base_module else "default",
        "author": sanitize_text(input("Enter your name or nickname: ")),
        "requires": {
            "fpp": f">={str(version()).strip('v')}",
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
            typer.echo(typer.style(f"Missing {info}... Ignoring manifest entry.", fg=typer.colors.YELLOW))
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

    register_config = "@register_config()"
    extend_config = ""
    if extends:
        extend_config_import = f"{base.import_name if base else 'modules.' + extend_id}.config"
        extend_config_name = f"{_config_name(base.name) if base else _config_name(extend_id)}Config"
        config_import = f"""from flaskpp.app.config import register_config
from {extend_config_import} import {extend_config_name}\n\n"""
        extend_config = f"({extend_config_name})"

    elif base_module:
        config_import = ""
        register_config = ""

    else:
        config_import = "from flaskpp.app.config import register_config\n\n"

    (module_dst / "config.py").write_text(
        creator_templates.module_config.format(
            config_import=config_import,
            register=register_config,
            extends=extend_config,
            name=_config_name(mod_id)
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
    base_extensions = base.required_extensions if base else []
    for extension in creator_templates.extensions:
        require = prompt_yes_no(f"Do you want to use {extension} in this module? (y/N) ")

        if extension == "sqlalchemy" and (require or extension in base_extensions):
            data = module_dst / "data"
            data.mkdir(exist_ok=True)
            if not base_module:
                (data / "__init__.py").write_text(creator_templates.module_data_init)

        if not require:
            continue

        required.append(f'"{extension}"')

    requires = ""
    if required:
        requires = f"""\n\trequired_extensions=[
        {",\n\t\t".join(required)}
    ],"""

    (module_dst / "__init__.py").write_text(
        creator_templates.module_init.format(
            extend_import=extend_import,
            extend=f"\n\textends={extend}," if extends else "",
            requires=requires,
            is_base="\n\tis_base=True" if base_module else ""
        )
    )

    typer.echo(typer.style(
        f"Module '{module_name}' has been successfully created.",
        fg=typer.colors.GREEN, bold=True
    ))
