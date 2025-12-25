from secrets import token_hex
from pathlib import Path
from configparser import ConfigParser
import typer, os

from flaskpp.utils import prompt_yes_no
from flaskpp.modules import generate_modlib

counting_map = {
    1: "st",
    2: "nd",
    3: "rd"
}

conf_path = Path.cwd() / "app_configs"


def base_config():
    return {
        "core": {
            "default_SERVER_NAME": "localhost",
            "protected_SECRET_KEY": token_hex(256),
        },

        "database": {
            "default_DATABASE_URL": "sqlite:///appdata.db",
        },

        "redis": {
            "default_REDIS_URL": "redis://redis:6379",
        },

        "babel": {
            "default_SUPPORTED_LOCALES": "en;de",
        },

        "security": {
            "protected_SECURITY_PASSWORD_SALT": token_hex(32),
        },

        "mail": {
            "MAIL_SERVER": "",
            "default_MAIL_PORT": 25,
            "default_MAIL_USE_TLS": True,
            "default_MAIL_USE_SSL": False,
            "MAIL_USERNAME": "",
            "MAIL_PASSWORD": "",
            "default_MAIL_DEFAULT_SENDER": "noreply@example.com",
        },

        "jwt": {
            "protected_JWT_SECRET_KEY": token_hex(64),
        },

        "extensions": {
            "default_EXT_SQLALCHEMY": 1,
            "default_EXT_SOCKET": 1,
            "EXT_BABEL": 0,
            "EXT_FST": 0,
            "EXT_AUTHLIB": 0,
            "EXT_MAILING": 0,
            "EXT_CACHE": 0,
            "EXT_API": 0,
            "EXT_JWT_EXTENDED": 0,
        },

        "features": {
            "default_FPP_PROCESSING": 1,
            "default_FRONTEND_ENGINE": 1,
        },

        "dev": {
            "DB_AUTOUPDATE": 0,
        }
    }


def welcome():
    typer.echo("\n------------------ " +
               typer.style("Flask++ Setup", bold=True) +
               " ------------------\n")
    typer.echo("Thank your for using our little foundation to build")
    typer.echo("your new app! We will try our best to get you ready")
    typer.echo("within the next two minutes. 💚  Start a timer! ;)\n")
    typer.echo("      " +
               typer.style("~ GrowVolution 2025 - MIT License ~", fg=typer.colors.CYAN, bold=True) +
               "\n")
    typer.echo("---------------------------------------------------")
    typer.echo("\n")


def app_name(app_number):
    ans = input(typer.style("Enter the name of your "
                            f"{app_number}{counting_map.get(app_number, 'th')} app: ",
                            bold=True)).strip()
    if not ans:
        ans = f"app{app_number}"
    return ans


def setup_app(app_number):
    config = ConfigParser()
    config.optionxform = str

    app = app_name(app_number)
    conf = conf_path / f"{app}.conf"
    conf_exists = conf.exists()
    if conf_exists:
        config.read(conf)

    typer.echo(typer.style("Okay, let's setup your app config.\n", fg=typer.colors.YELLOW, bold=True) +
               typer.style("Leave blank to stick with the defaults.", fg=typer.colors.MAGENTA))

    for k, v in base_config().items():
        if k not in config:
            config[k] = {}
        for key, value in v.items():
            if key.startswith("protected_"):
                key = key.removeprefix("protected_")
                if not (conf_exists and config[k].get(key)):
                    config[k][key] = str(value)
                continue

            if key.startswith("default_"):
                key = key.removeprefix("default_")
                input_prompt = f"{key} ({value}): "
            else:
                input_prompt = f"{key}: "

            val = input(input_prompt).strip()
            if not val:
                val = str(value)
            config[k][key] = val

    with open(conf, "w") as f:
        config.write(f)

    generate_modlib(app)

    typer.echo(typer.style(
        f"Okay, you have successfully created {app}. 🥳",
        fg=typer.colors.GREEN, bold=True
    ) + "\n")

    register_app = prompt_yes_no(typer.style(
        f"Do you want to register {app} as a service? (y/N): ",
        fg=typer.colors.MAGENTA, bold=True
    ) + "\n")

    if register_app:
        from .service_registry import register
        try:
            port_input = input("On which port do you want your service to run? (5000): ").strip()
            port = int(port_input) if port_input else 5000
        except ValueError:
            port = 5000
        debug = prompt_yes_no("Do you want your service to run in debug mode? (y/N): ")

        register(app, port, debug)

        typer.echo(typer.style(
            f"Okay, you have successfully registered {app} as a service. 🚀",
            fg=typer.colors.GREEN, bold=True
        ) + "\n\n")
    else:
        typer.echo("")


def setup():
    welcome()

    i = len(list(conf_path.glob("*.conf"))) + 1
    setup_app(i)

    i += 1
    while prompt_yes_no(f"Do you want to create a {i}{counting_map.get(i, 'th')} app? (y/N): "):
        setup_app(i)
        i += 1

    typer.echo(f"\n---------------- " +
               typer.style("Setup complete.", bold=True) +
               " ----------------\n")
    typer.echo("You can now run and manage your app(s) with: \n" +
               typer.style("fpp run [args]", fg=typer.colors.GREEN, bold=True))
    typer.echo("To create more apps, just run this script again.")
    typer.echo("The settings of your app(s) can be managed in:\n" +
               typer.style("app_configs/*.conf", fg=typer.colors.MAGENTA, bold=True) +
               "\n")
    typer.echo("----------------- " +
               typer.style("Happy coding!", fg=typer.colors.CYAN, bold=True) +
               " -----------------")


def setup_entry(app: typer.Typer):
    app.command()(setup)
