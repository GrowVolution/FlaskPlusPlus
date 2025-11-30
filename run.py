from pathlib import Path
from configparser import ConfigParser
from datetime import datetime
from colorama import Fore, Style
from argparse import ArgumentParser
import subprocess, sys, os, signal

root_path = Path(__file__).parent
conf_path = root_path / "app_configs"
logs_path = root_path / "logs"

apps: dict[str, dict] = {}


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
    print(f"{Fore.MAGENTA}{Style.BRIGHT}Starting {app_name}...{Style.RESET_ALL}")
    raw = input(f"On which port do you want this app to run? ({suggested}): ").strip()
    try:
        port = int(raw) if raw else suggested
    except ValueError:
        port = suggested
    next_default = port + 1
    return port, next_default


def _promt_debug() -> str:
    choice = input("Start app in debug mode? (y/N): ").strip().lower()
    return "1" if choice in {"y", "yes", "1"} else "0"


def start_app(conf_file: Path, default_port: int, reload: bool = False) -> int:
    app_name = conf_file.stem
    base_env = _env_from_conf(conf_file)
    base_env["APP_NAME"] = app_name
    if reload and app_name in apps:
        port = apps[app_name]["port"]
        base_env["DEBUG_MODE"] = apps[app_name].get("debug", "0")
        next_default = port + 1
    else:
        port, next_default = _prompt_port(app_name, default_port) if args.interactive else (default_port, None)
        debug = args.debug if args.debug or not args.interactive else _promt_debug()
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
    print(f"{app_name} is running on http://0.0.0.0:{port}\n")
    return next_default


def stop_app(app_name: str):
    entry = apps.get(app_name)
    if not entry or not entry["proc"]:
        print(f"{Fore.RED}{Style.BRIGHT}{app_name} is not running.{Style.RESET_ALL}")
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
    print(f"{Fore.GREEN}{Style.BRIGHT}{app_name} has been stopped.{Style.RESET_ALL}")


def reload_app(app_name: str):
    entry = apps.get(app_name)
    if not entry or not entry["proc"]:
        print(f"{Fore.RED}{Style.BRIGHT}{app_name} is not running.{Style.RESET_ALL}")
        return
    port = entry["port"] or 5000
    stop_app(app_name)
    start_app(entry["conf"], port, reload=True)
    print(f"{Fore.GREEN}{Style.BRIGHT}{app_name} has been reloaded.{Style.RESET_ALL}")


def restart_app(app_name: str):
    entry = apps.get(app_name)
    if not entry:
        print(f"{Fore.YELLOW}{Style.BRIGHT}Unknown app: {app_name}{Style.RESET_ALL}")
        return
    port = entry["port"] or 5000
    stop_app(app_name)
    _ = start_app(entry["conf"], port)


def shutdown(signum = None, frame = None):
    prefix = "S"
    if signum:
        prefix = f"Handling signal SIG{'INT' if signum == signal.SIGINT else 'TERM'}, s"
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}{prefix}hutting down...{Style.RESET_ALL}")
    for app in apps:
        stop_app(app)
    print(f"{Style.BRIGHT}Thank you for playing the game of life... Bye!{Style.RESET_ALL}")
    sys.exit(0)


def create_apps():
    default_port = 5000
    for file in sorted(conf_path.glob("*.conf")):
        default_port = start_app(file, default_port)


def menu():
    print("\nChoose an action:\n"
          "\t1. Reload app\n"
          "\t2. Restart app\n"
          "\t3. Stop app\n"
          "\t4. Start app (if stopped)\n"
          "\t5. Clear console\n"
          "\t6. Exit")


def current_apps() -> list[str]:
    names = sorted(apps.keys())
    for idx, name in enumerate(names, start=1):
        status = f"{Fore.GREEN}running{Style.RESET_ALL}" if (
                apps[name]["proc"] and apps[name]["proc"].poll() is None
        ) else f"{Fore.RED}stopped{Style.RESET_ALL}"
        port = apps[name]["port"]
        port_s = f":{port}" if port else ""
        print(f"\t{idx}. {name} [{status}{port_s}]")
    return names


def main():
    prepare()
    print(f"\n{Style.BRIGHT}GrowVolution 2025 - App Control Script{Style.RESET_ALL}\n")
    print(f"{Fore.YELLOW}{Style.BRIGHT}Starting your apps...{Style.RESET_ALL}")
    create_apps()
    while True:
        print("\nYour apps:")
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
            print(f"{Fore.YELLOW}{Style.BRIGHT}Invalid option.{Style.RESET_ALL}")
            continue
        if not choices:
            print(f"{Fore.RED}{Style.BRIGHT}"
                  "No apps known. Put .conf files into app_configs/ and restart."
                  f"{Style.RESET_ALL}")
            continue
        print("Choose your target app by its number:")
        choice_raw = input("> ").strip()
        try:
            idx = int(choice_raw)
            if not (1 <= idx <= len(choices)):
                raise ValueError
            chosen_app = choices[idx - 1]
        except ValueError:
            print(f"{Fore.RED}{Style.BRIGHT}"
                  f"{choice_raw} is not a valid number."
                  f"{Style.RESET_ALL}")
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
                print(f"{Fore.RED}{Style.BRIGHT}"
                      f"{chosen_app} is already running."
                      f"{Style.RESET_ALL}")
            else:
                default = entry["port"] or 5000
                entry["port"] = None
                _ = start_app(entry["conf"], default)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    parser = ArgumentParser()
    parser.add_argument("-i", "--interactive", action="store_true")
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("-p", "--port", type=int, default=5000)
    parser.add_argument("-a", "--app", type=str, default='app1')

    args = parser.parse_args()
    if args.interactive:
        main()
    else:
        conf = conf_path / f"{args.app}.conf"
        start_app(conf, args.port)
        proc = apps[args.app]["proc"]
        while True:
            continue
