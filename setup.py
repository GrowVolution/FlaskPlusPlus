from secrets import token_hex
from pathlib import Path
from configparser import ConfigParser
from colorama import init, Fore, Style

from modules import generate_modlib

counting_map = {
    1: "st",
    2: "nd",
    3: "rd"
}

conf_path = Path(__file__).parent / "app_configs"
conf_path.mkdir(exist_ok=True)


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

        "features": {
            "default_EXT_SQLALCHEMY": 1,
            "EXT_SOCKET": 0,
            "EXT_BABEL": 0,
            "EXT_FST": 0,
            "EXT_AUTHLIB": 0,
            "EXT_MAILING": 0,
            "EXT_CACHE": 0,
            "EXT_API": 0,
            "EXT_JWT_EXTENDED": 0,
        },

        "dev": {
            "DB_AUTOUPDATE": 0,
        }
    }


def welcome():
    print( "\n--------------- "
          f"{Style.BRIGHT}FlaskSkeleton Setup{Style.RESET_ALL} "
           "---------------\n")
    print( "Thank your for using our little foundation to build")
    print( "your new app! We will try our best to get you ready")
    print( "within the next two minutes. 💚  Start a timer! ;)\n")
    print(f"        {Fore.CYAN}{Style.BRIGHT}"
           "~ GrowVolution 2025 - MIT License ~"
          f"{Style.RESET_ALL}\n")
    print( "---------------------------------------------------")
    print( "\n")


def app_name(app_number):
    ans = input(f"{Style.BRIGHT}Enter the name of your "
                f"{app_number}{counting_map.get(app_number, 'th')} app: "
                f"{Style.RESET_ALL}").strip()
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

    print(f"{Fore.YELLOW}{Style.BRIGHT}Okay, let's setup your app config.\n"
          f"{Fore.MAGENTA}Leave blank to stick with the defaults.{Style.RESET_ALL}")

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

    print(f"{Fore.GREEN}{Style.BRIGHT}"
          f"Okay, you have successfully created {app}. 🥳"
          f"{Style.RESET_ALL}\n")

    if (input(f"{Fore.MAGENTA}{Style.BRIGHT}"
              f"Do you want to register {app} as a service? (y/N): "
              f"{Style.RESET_ALL}\n").lower().strip() in ["yes", "y", "1"]):
        from utils.service_registry import register
        try:
            port_input = input("On which port do you want your service to run? (5000): ").strip()
            port = int(port_input) if port_input else 5000
        except ValueError:
            port = 5000
        debug = (input("Do you want your service to run in debug mode? (y/N): ")
                 .lower().strip() in ["yes", "y", "1"])
        register(app, port, debug)
        print(f"{Fore.GREEN}{Style.BRIGHT}"
              f"Okay, you have successfully registered {app} as a service. 🚀"
              f"{Style.RESET_ALL}\n\n")
    else:
        print()


def setup():
    welcome()

    i = len(list(conf_path.glob("*.conf"))) + 1
    setup_app(i)

    i += 1
    while (input(f"Do you want to create a {i}{counting_map.get(i, 'th')} app? (y/N): ")
        .lower().strip()) in ["yes", "y", "1"]:
        setup_app(i)
        i += 1

    print(f"\n---------------- {Style.BRIGHT}Setup complete."
          f"{Style.RESET_ALL} ----------------\n")
    print( "You can now run and manage your app(s) with: \n"
          f"(.venv) {Fore.GREEN}{Style.BRIGHT}python run.py{Style.RESET_ALL}")
    print( "To create more apps, just run this script again.")
    print( "The settings of your app(s) can be managed in:\n"
          f"{Fore.MAGENTA}{Style.BRIGHT}app_configs/*.conf{Style.RESET_ALL}\n")
    print(f"----------------- {Fore.CYAN}{Style.BRIGHT}"
          f"Happy coding!{Style.RESET_ALL} -----------------")


if __name__ == "__main__":
    init(autoreset=True)
    setup()
