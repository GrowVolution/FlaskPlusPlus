from flask import Flask
from jinja2 import ChoiceLoader, PrefixLoader, FileSystemLoader
from pathlib import Path
from importlib import import_module
from configparser import ConfigParser
from colorama import Fore, Style
from functools import wraps
import os

from utils.debugger import log, exception

module_home = Path(__file__).parent
conf_path = module_home.parent / "app_configs"


def require_extensions(*extensions):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for ext in extensions:
                if not isinstance(ext, str):
                    log("warn", f"Invalid extension '{ext}'.")
                    continue

                from app.utils import enabled
                if not enabled(f"EXT_{ext.upper()}"):
                    raise RuntimeError(f"Extension '{ext}' is not enabled.")
            return func(*args, **kwargs)

        return wrapper
    return decorator


def generate_modlib(app_name: str):
    conf = conf_path / f"{app_name}.conf"
    config = ConfigParser()
    config.optionxform = str

    if conf.exists():
        config.read(conf)
    if "modules" not in config:
        config["modules"] = {}

    print(f"\n{Fore.YELLOW}{Style.BRIGHT}"
          f"Okay, now you can activate your installed modules.\n"
          f"{Fore.MAGENTA}Default is '0' (deactivated)!"
          f"{Style.RESET_ALL}")

    for obj in module_home.iterdir():
        if obj.is_dir() and (obj / "__init__.py").exists():
            val = input(f"{obj.name}: ").strip()
            if not val:
                val = "0"
            config["modules"][obj.name] = val

    set_home = input(f"\n{Fore.YELLOW}{Style.BRIGHT}"
                     "Do you want to define a home module?"
                     f"{Style.RESET_ALL} (Y/n): ").lower().strip()
    if set_home not in {"n", "no", "0"}:
        print(f"{Fore.MAGENTA}{Style.BRIGHT}Okay choose your home module:{Style.RESET_ALL}")

        choices = list(config["modules"].keys())
        for idx, module in enumerate(choices, start=1):
            print(f"\t{Style.BRIGHT}{idx}. {module}{Style.RESET_ALL}")

        while True:
            choice = input("> ").strip()
            try:
                choice = int(choice) - 1
                home = choices[choice]
                break
            except (ValueError, IndexError):
                print(f"{Fore.RED}{Style.BRIGHT}Invalid input. Try again:{Style.RESET_ALL}")

        config["modules"]["HOME_MODULE"] = home

    with open(conf, "w") as f:
        config.write(f)


def register_modules(app: Flask):
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
        except ModuleNotFoundError:
            log("error", f"Could not import module '{mod_name}' for app '{app_name}'.")
            continue

        register = getattr(mod, "register_module", None)
        if not callable(register):
            log("error", f"Missing 'register_module(app: Flask)' in module '{mod_name}'.")
            continue

        try:
            home = os.getenv("HOME_MODULE", "").lower() == mod_name.lower()
            register(app, home)
            loader_context[mod_name] = FileSystemLoader(f"modules/{mod_name}/templates")
            if home:
                primary_loader = loader_context[mod_name]
            log("info", f"Registered module '{mod_name}' as {'home' if home else 'path'}.")
        except Exception as e:
            exception(e, f"Failed registering module '{mod_name}'.")

    loaders = []
    if primary_loader:
        loaders.append(primary_loader)
    loaders.append(PrefixLoader(loader_context))
    loaders.append(FileSystemLoader(f"app/templates"))

    app.jinja_loader = ChoiceLoader(loaders)
