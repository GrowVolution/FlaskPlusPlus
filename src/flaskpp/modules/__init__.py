from jinja2 import ChoiceLoader, PrefixLoader, FileSystemLoader
from pathlib import Path
from importlib import import_module
from configparser import ConfigParser
from typing import TYPE_CHECKING
import os, typer, json

from flaskpp.cli import cwd
from flaskpp.module import basic_checked_data, valid_version
from flaskpp.utils import enabled
from flaskpp.utils.debugger import log, exception
from flaskpp.exceptions import ManifestError

if TYPE_CHECKING:
    from flask import Flask
    from flaskpp import FlaskPP

module_home = cwd / "modules"
conf_path = cwd / "app_configs"
_modules = {}


def generate_modlib(app_name: str):
    conf = conf_path / f"{app_name}.conf"
    config = ConfigParser()
    config.optionxform = str

    conf_exists = conf.exists()
    if conf_exists:
        config.read(conf)
    if "modules" not in config:
        config["modules"] = {}

    typer.echo("\n" +
               typer.style("Okay, now you can activate your installed modules.\n", fg=typer.colors.YELLOW, bold=True) +
               typer.style("Default is '0' (deactivated)!", fg=typer.colors.MAGENTA))

    for module in installed_modules(module_home, False):
        mod_id = module[0]
        val = input(f"<{mod_id} {module[1]}>: ").strip()
        if not val:
            val = "0"
        config["modules"][mod_id] = val

        if enabled(val):
            from flaskpp.utils.setup import setup_config
            try:
                conf = import_module(f"modules.{module[2]}.config")
                module_config = getattr(conf, "module_config", None)
                if not module_config:
                    raise ImportError()

                base_config = module_config()
                if not base_config:
                    raise ImportError()

                base = {
                    mod_id: base_config
                }
                setup_config(config, base, conf_exists)
                typer.echo("\n")
            except (ModuleNotFoundError, ImportError, TypeError):
                pass

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
                home_module = choices[choice]
                break
            except (ValueError, IndexError):
                typer.echo(typer.style(
                    "Invalid input. Try again:",
                    fg=typer.colors.RED,
                    bold=True
                ))

        config["modules"]["HOME_MODULE"] = home_module

    with open(conf, "w") as f:
        config.write(f)


def register_modules(app: "FlaskPP | Flask"):
    app_name = os.getenv("APP_NAME")
    if not app_name:
        raise RuntimeError("Missing app name variable: APP_NAME")

    loader_context = {}
    primary_loader = None

    def register():
        nonlocal loader_context, primary_loader

        for module in installed_modules(Path(app.root_path) / "modules", False):
            mod_id = module[0]
            if not enabled(mod_id):
                continue

            try:
                mod = import_module(f"modules.{module[2]}")
            except ModuleNotFoundError as e:
                exception(e, f"Could not import module '{mod_id}' for app '{app_name}'.")
                continue

            from flaskpp import Module
            module = getattr(mod, "module", None)
            if not isinstance(module, Module):
                log("error", f"Missing 'module: Module' in module '{mod_id}'.")
                continue

            try:
                log("info", f"Registering: {module}")
            except ManifestError as e:
                exception(e, f"Failed to log {mod_id}.module")
                continue

            try:
                is_home = os.getenv("HOME_MODULE", "").lower() == mod_id
                module.enable(app, is_home)
                loader_context[module.name] = FileSystemLoader(f"modules/{mod_id}/templates")
                if is_home:
                    primary_loader = loader_context[module.name]
                log("info", f"Registered module '{module.module_name}' as {'home' if is_home else 'path'}.")
            except Exception as e:
                exception(e, f"Failed registering module '{module.module_name}'.")

    if enabled("FPP_MODULES"): register()

    loaders = []
    if primary_loader:
        loaders.append(primary_loader)
    loaders.append(FileSystemLoader("templates"))
    loaders.append(PrefixLoader(loader_context))
    loaders.append(
        FileSystemLoader(str((Path(__file__).parent.parent / "app" / "templates").resolve()))
    )

    app.jinja_loader = ChoiceLoader(loaders)


def installed_modules(package: Path, do_log: bool = True) -> list[tuple[str, str, str]]:
    if _modules.get(package):
        return _modules[package]

    if not package.name == "modules":
        raise ValueError(f"Invalid package name '{package.name}'.")

    _modules[package] = []

    for module in package.iterdir():
        if not module.is_dir():
            continue

        try:
            manifest = module / "manifest.json"
            module_data = basic_checked_data(manifest)
            version = valid_version(module_data["version"])
            _modules[package].append(
                (module_data.get("id", module.name), version, module.name)
            )
        except (ModuleNotFoundError, FileNotFoundError, AttributeError, ManifestError, json.JSONDecodeError) as e:
            if do_log: log("warn", f"Invalid module package '{module.name}' in {package}: {e}.")
            continue

    return _modules[package]
