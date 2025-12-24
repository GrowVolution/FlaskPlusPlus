from jinja2 import ChoiceLoader, PrefixLoader, FileSystemLoader
from pathlib import Path
from importlib import import_module
from configparser import ConfigParser
import os, typer

from flaskpp.utils.debugger import log, exception

home = Path.cwd()
module_home = home / "modules"
conf_path = home / "app_configs"


def generate_modlib(app_name: str):
    conf = conf_path / f"{app_name}.conf"
    config = ConfigParser()
    config.optionxform = str

    if conf.exists():
        config.read(conf)
    if "modules" not in config:
        config["modules"] = {}

    typer.echo("\n" +
               typer.style("Okay, now you can activate your installed modules.\n", fg=typer.colors.YELLOW, bold=True) +
               typer.style("Default is '0' (deactivated)!", fg=typer.colors.MAGENTA))

    for obj in module_home.iterdir():
        if obj.is_dir() and (obj / "__init__.py").exists():
            val = input(f"{obj.name}: ").strip()
            if not val:
                val = "0"
            config["modules"][obj.name] = val

    set_home = input(
        "\n" +
        typer.style("Do you want to define a home module?", fg=typer.colors.YELLOW, bold=True) +
        " (Y/n): "
    ).lower().strip()

    if set_home not in {"n", "no", "0"}:
        typer.echo(typer.style(
            "Okay choose your home module:",
            fg=typer.colors.MAGENTA,
            bold=True
        ))

        choices = list(config["modules"].keys())
        for idx, module in enumerate(choices, start=1):
            typer.echo("\t" + typer.style(f"{idx}. {module}", bold=True))

        while True:
            choice = input("> ").strip()
            try:
                choice = int(choice) - 1
                home = choices[choice]
                break
            except (ValueError, IndexError):
                typer.echo(typer.style(
                    "Invalid input. Try again:",
                    fg=typer.colors.RED,
                    bold=True
                ))

        config["modules"]["HOME_MODULE"] = home

    with open(conf, "w") as f:
        config.write(f)


def register_modules(app):
    app_name = os.getenv("APP_NAME")
    if not app_name:
        raise RuntimeError("Missing app name variable: APP_NAME")

    conf = conf_path / f"{app_name}.conf"
    if not conf.exists():
        raise RuntimeError(f"Missing modlib for '{app_name}'.")

    config = ConfigParser()
    config.optionxform = str
    config.read(conf)

    if "modules" not in config:
        log("warn", f"Missing [modules] section in '{app_name}.conf'.")
        return

    loader_context = {}
    primary_loader = None
    for mod_name, setting in config["modules"].items():
        enabled = setting.strip().lower() in ["true", "1", "yes"]
        if not enabled:
            continue

        try:
            mod = import_module(f"modules.{mod_name}")
        except ModuleNotFoundError as e:
            exception(e, f"Could not import module '{mod_name}' for app '{app_name}'.")
            continue

        from flaskpp import Module
        module = getattr(mod, "module", None)
        if not isinstance(module, Module):
            log("error", f"Missing 'module: Module' in module '{mod_name}'.")
            continue

        try:
            log("info", f"Registering: {module}")
        except ManifestError as e:
            exception(e, f"Failed to log {mod_name}.module")
            continue

        try:
            home = os.getenv("HOME_MODULE", "").lower() == mod_name.lower()
            module.enable(app, home)
            loader_context[mod_name] = FileSystemLoader(f"modules/{mod_name}/templates")
            if home:
                primary_loader = loader_context[mod_name]
            log("info", f"Registered module '{mod_name}' as {'home' if home else 'path'}.")
        except Exception as e:
            exception(e, f"Failed registering module '{mod_name}'.")

    loaders = []
    if primary_loader:
        loaders.append(primary_loader)
    loaders.append(FileSystemLoader("templates"))
    loaders.append(PrefixLoader(loader_context))
    loaders.append(
        FileSystemLoader(str((Path(__file__).parent.parent / "app" / "templates").resolve()))
    )

    app.jinja_loader = ChoiceLoader(loaders)


class ModuleError(Exception):
    pass


class ManifestError(ModuleError):
    pass
