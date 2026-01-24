from pathlib import Path
import typer, os, sys, ctypes, subprocess, shlex, plistlib

home = Path.cwd().resolve()
service_path = home / "services"

registry = typer.Typer(help="Manage OS-level services for Flask++ apps.")


def _ensure_admin() -> bool:
    if os.name == "nt":
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    return os.geteuid() == 0


def service_file(app: str) -> Path:
    if os.name == "nt":
        return service_path / f"{app}.py"
    if sys.platform == "darwin":
        return service_path / f"{app}.plist"
    return service_path / f"{app}.service"


def create_service(app_name: str, port: int, debug: bool):
    args = [sys.executable, "-m", "flaskpp", "run", "--app", app_name, "--port", str(port)]
    if debug:
        args.append("--debug")

    if os.name == "nt":
        entry_list = ", ".join(repr(a) for a in args)
        template = f"""
import win32serviceutil, win32service, win32event, servicemanager, subprocess, time

class AppService(win32serviceutil.ServiceFramework):
    _svc_name_ = "{app_name} Service"
    _svc_display_name_ = "{app_name} Background Service"
    _svc_description_ = "Runs the {app_name} backend as a persistent service."

    def __init__(self, args):
        super().__init__(args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.alive = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.alive = False

    def SvcDoRun(self):
        self.main_loop()

    def main_loop(self):
        proc = subprocess.Popen([{entry_list}], cwd=r"{str(home)}")
        while self.alive:
            if proc.poll() is not None:
                raise RuntimeError("Service execution failed.")
            time.sleep(1)
        proc.terminate()

if __name__ == "__main__":
    win32serviceutil.HandleCommandLine(AppService)
"""
        out = service_file(app_name)
        out.write_text(template)

    elif sys.platform == "darwin":
        plist = {
            "Label": f"flaskpp.{app_name}",
            "ProgramArguments": args,
            "WorkingDirectory": str(home),
            "RunAtLoad": True,
            "KeepAlive": True,
            "StandardOutPath": str(home / f"{app_name}.out.log"),
            "StandardErrorPath": str(home / f"{app_name}.err.log"),
        }
        out = service_file(app_name)
        with out.open("wb") as f:
            plistlib.dump(plist, f)

    else:
        exec_start = " ".join(shlex.quote(a) for a in args)
        user = str(home).split("/")[1] if str(home).startswith("/home/") else "root"
        template = f"""
[Unit]
Description={app_name} Service
After=network.target

[Service]
User={user}
ExecStart={exec_start}
WorkingDirectory={str(home)}
Type=simple
Restart=on-failure

[Install]
WantedBy=multi-user.target
"""
        out = service_file(app_name)
        out.write_text(template)
        target = Path(f"/etc/systemd/system/{app_name}.service")
        if target.exists() or target.is_symlink():
            target.unlink()
        target.symlink_to(out)


@registry.command()
def register(app: str = typer.Option(..., "--app", "-a"),
             port: int = typer.Option(5000, "--port", "-p"),
             debug: bool = typer.Option(False, "--debug", "-d")):
    if not _ensure_admin():
        raise typer.Exit(1)

    if not (app and (home / "app_configs" / f"{app}.conf").exists()):
        raise typer.Exit(1)

    create_service(app, port, debug)

    if os.name == "nt":
        f = service_file(app)
        subprocess.run([sys.executable, str(f), "install"], check=False)
        subprocess.run([sys.executable, str(f), "start"], check=False)
    elif sys.platform == "darwin":
        f = service_file(app)
        target = Path.home() / "Library" / "LaunchAgents" / f.name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            target.unlink()
        target.symlink_to(f)
        subprocess.run(["launchctl", "load", str(target)], check=False)
    else:
        subprocess.run(["systemctl", "daemon-reload"], check=False)
        subprocess.run(["systemctl", "enable", app], check=False)
        subprocess.run(["systemctl", "start", app], check=False)


@registry.command()
def start(app: str):
    if os.name == "nt":
        f = service_file(app)
        subprocess.run([sys.executable, str(f), "start"], check=False)
    elif sys.platform == "darwin":
        subprocess.run(["launchctl", "start", f"flaskpp.{app}"], check=False)
    else:
        subprocess.run(["systemctl", "start", app], check=False)


@registry.command()
def stop(app: str):
    if os.name == "nt":
        f = service_file(app)
        subprocess.run([sys.executable, str(f), "stop"], check=False)
    elif sys.platform == "darwin":
        subprocess.run(["launchctl", "stop", f"flaskpp.{app}"], check=False)
    else:
        subprocess.run(["systemctl", "stop", app], check=False)


@registry.command()
def remove(app: str):
    if not _ensure_admin():
        raise typer.Exit(1)

    if os.name == "nt":
        f = service_file(app)
        subprocess.run([sys.executable, str(f), "stop"], check=False)
        subprocess.run([sys.executable, str(f), "remove"], check=False)
        f.unlink(missing_ok=True)

    elif sys.platform == "darwin":
        target = Path.home() / "Library" / "LaunchAgents" / f"{app}.plist"
        subprocess.run(["launchctl", "unload", str(target)], check=False)
        target.unlink(missing_ok=True)
        service_file(app).unlink(missing_ok=True)

    else:
        subprocess.run(["systemctl", "stop", app], check=False)
        subprocess.run(["systemctl", "disable", app], check=False)
        service_file(app).unlink(missing_ok=True)
        subprocess.run(["systemctl", "daemon-reload"], check=False)


def registry_entry(app: typer.Typer):
    app.add_typer(registry, name="registry")
