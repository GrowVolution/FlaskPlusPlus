from pathlib import Path
from configparser import ConfigParser
from datetime import datetime
import subprocess, sys, os, signal
import typer

from flaskpp.utils import prompt_yes_no

root_path = Path.cwd()
conf_path = root_path / "app_configs"
logs_path = root_path / "logs"

apps: dict[str, dict] = {}
args: dict = {}


def prepare():
    conf_path.mkdir(parents=True, exist_ok=True)
    logs_path.mkdir(parents=True, exist_ok=True)
    if not any(conf_path.glob("*.conf")):
        subprocess.run([sys.executable, str(root_path / "setup.py")], check=True)


def _env_from_conf(conf_file: Path) -> dict:
    env = os.environ.copy()
    cfg = ConfigParser()
    cfg.optionxform = str
    cfg.read(conf_file)
    for k, v in cfg.defaults().items():
        env[k] = v
    for section in cfg.sections():
        for k, v in cfg[section].items():
            env[k] = v
    return env


def _ensure_log_file(app_name: str) -> Path:
    app_log_dir = logs_path / app_name
    app_log_dir.mkdir(parents=True, exist_ok=True)
    return app_log_dir / f"{datetime.now().strftime('%Y%m%d%H%M')}.log"


def _prompt_port(app_name: str, suggested: int) -> tuple[int, int]:
    typer.echo(typer.style(f"Starting {app_name}...", fg=typer.colors.MAGENTA, bold=True))
    raw = input(f"On which port do you want this app to run? ({suggested}): ").strip()
    try:
        port = int(raw) if raw else suggested
    except ValueError:
        port = suggested
    next_default = port + 1
    return port, next_default


def start_app(conf_file: Path, default_port: int, reload: bool = False) -> int:
    app_name = conf_file.stem
    base_env = _env_from_conf(conf_file)
    base_env["APP_NAME"] = app_name

    if reload and app_name in apps:
        port = apps[app_name]["port"]
        base_env["DEBUG_MODE"] = apps[app_name].get("debug", "0")
        next_default = port + 1
    else:
        if args["interactive"]:
            port, next_default = _prompt_port(app_name, default_port)
            debug = args["debug"] or prompt_yes_no("Start app in debug mode? (y/N): ")
        else:
            port, next_default = default_port, None
            debug = args["debug"]
        base_env["DEBUG_MODE"] = "1" if debug else "0"

    base_env["SERVER_PORT"] = str(port)
    log_file = _ensure_log_file(app_name)

    proc = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "--host", "0.0.0.0",
            "--port", f"{port}",
            "main:app",
        ],
        stdout=open(log_file, "w"),
        stderr=subprocess.STDOUT,
        env=base_env,
        cwd=str(root_path)
    )

    apps[app_name] = {"proc": proc, "port": port, "conf": conf_file, "debug": base_env["DEBUG_MODE"]}

    typer.echo(f"{app_name} is running on http://0.0.0.0:{port}\n")
    return next_default


def stop_app(app_name: str):
    entry = apps.get(app_name)
    if not entry or not entry["proc"]:
        typer.echo(typer.style(f"{app_name} is not running.", fg=typer.colors.RED, bold=True))
        return
    proc = entry["proc"]
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
    entry["proc"] = None
    typer.echo(typer.style(f"{app_name} has been stopped.", fg=typer.colors.GREEN, bold=True))


def reload_app(app_name: str):
    entry = apps.get(app_name)
    if not entry or not entry["proc"]:
        typer.echo(typer.style(f"{app_name} is not running.", fg=typer.colors.RED, bold=True))
        return
    port = entry["port"] or 5000
    stop_app(app_name)
    start_app(entry["conf"], port, reload=True)
    typer.echo(typer.style(f"{app_name} has been reloaded.", fg=typer.colors.GREEN, bold=True))


def restart_app(app_name: str):
    entry = apps.get(app_name)
    if not entry:
        typer.echo(typer.style(f"Unknown app: {app_name}", fg=typer.colors.YELLOW, bold=True))
        return
    port = entry["port"] or 5000
    stop_app(app_name)
    _ = start_app(entry["conf"], port)


def shutdown(signum=None, frame=None):
    prefix = "S"
    if signum:
        prefix = f"Handling signal SIG{'INT' if signum == signal.SIGINT else 'TERM'}, s"
    typer.echo(typer.style(f"\n{prefix}hutting down...", fg=typer.colors.YELLOW, bold=True))
    for app in apps:
        stop_app(app)
    typer.echo(typer.style("Thank you for playing the game of life... Bye!", bold=True))
    sys.exit(0)


def create_apps():
    default_port = 5000
    for file in sorted(conf_path.glob("*.conf")):
        default_port = start_app(file, default_port)


def menu():
    typer.echo(
        "\nChoose an action:\n"
        "\t1. Reload app\n"
        "\t2. Restart app\n"
        "\t3. Stop app\n"
        "\t4. Start app (if stopped)\n"
        "\t5. Clear console\n"
        "\t6. Exit"
    )


def current_apps() -> list[str]:
    names = sorted(apps.keys())
    for idx, name in enumerate(names, start=1):
        running = apps[name]["proc"] and apps[name]["proc"].poll() is None
        status = typer.style("running", fg=typer.colors.GREEN) if running else typer.style("stopped", fg=typer.colors.RED)
        port = apps[name]["port"]
        port_s = f":{port}" if port else ""
        typer.echo(f"\t{idx}. {name} [{status}{port_s}]")
    return names


def interactive_main():
    prepare()
    typer.echo(typer.style("Flask++ - App Control Script\n", bold=True))
    typer.echo(typer.style("Starting your apps...", fg=typer.colors.YELLOW, bold=True))
    create_apps()

    while True:
        typer.echo("\nYour apps:")
        choices = current_apps()
        menu()
        cmd = input("> ").strip()
        if cmd == "5":
            os.system("cls" if os.name == "nt" else "clear")
            continue
        if cmd == "6":
            shutdown()
            sys.exit(0)
        if cmd not in {"1", "2", "3", "4"}:
            typer.echo(typer.style("Invalid option.", fg=typer.colors.RED, bold=True))
            continue
        if not choices:
            typer.echo(typer.style(
                "No apps known. Put .conf files into app_configs/ and restart.",
                fg=typer.colors.RED,
                bold=True
            ))
            continue

        typer.echo("Choose your target app by its number:")
        choice_raw = input("> ").strip()
        try:
            idx = int(choice_raw)
            if not (1 <= idx <= len(choices)):
                raise ValueError
            chosen_app = choices[idx - 1]
        except ValueError:
            typer.echo(typer.style(f"{choice_raw} is not a valid number.", fg=typer.colors.RED, bold=True))
            continue

        if cmd == "1":
            reload_app(chosen_app)
        elif cmd == "2":
            restart_app(chosen_app)
        elif cmd == "3":
            stop_app(chosen_app)
        elif cmd == "4":
            entry = apps[chosen_app]
            if entry["proc"] and entry["proc"].poll() is None:
                typer.echo(typer.style(f"{chosen_app} is already running.", fg=typer.colors.RED, bold=True))
            else:
                default = entry["port"] or 5000
                entry["port"] = None
                _ = start_app(entry["conf"], default)


def run(
    interactive: bool = typer.Option(False, "-i", "--interactive"),
    debug: bool = typer.Option(False, "-d", "--debug"),
    port: int = typer.Option(5000, "-p", "--port"),
    app: str = typer.Option("app1", "-a", "--app")
):
    args["interactive"] = interactive
    args["debug"] = debug
    args["port"] = port
    args["app"] = app

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    if args["interactive"]:
        interactive_main()
    else:
        conf = conf_path / f"{args['app']}.conf"
        start_app(conf, args["port"])
        while True:
            continue


def run_entry(app: typer.Typer):
    app.command()(run)
