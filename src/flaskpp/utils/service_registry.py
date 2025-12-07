from pathlib import Path
import typer, os, sys, ctypes

home = Path(os.getcwd())
service_path = home / "services"
service_path.mkdir(exist_ok=True)

registry = typer.Typer(help="Manage OS-level services for Flask++ apps.")


def _ensure_admin() -> bool:
    if os.name == "nt":
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    return os.geteuid() == 0


def _service_file(app: str):
    return service_path / (f"{app}.py" if os.name == "nt" else f"{app}.service")


def create_service(app_name: str, port: int, debug: bool):
    entry = f"{sys.executable} -m flaskpp run --app {app_name} --port {port} {'--debug' if debug else ''}"

    if os.name == "nt":
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
        servicemanager.LogInfoMsg("{app_name} Service stopped.")

    def SvcDoRun(self):
        servicemanager.LogInfoMsg("{app_name} Service started.")
        self.main_loop()

    def main_loop(self):
        proc = subprocess.Popen(["cmd", "/C", "{entry}"])
        while self.alive:
            if proc.poll() is not None:
                raise RuntimeError("Service execution failed.")
            time.sleep(1)
        proc.terminate()

if __name__ == "__main__":
    win32serviceutil.HandleCommandLine(AppService)
"""
        out = _service_file(app_name)
        out.write_text(template)

    else:
        template = f"""
[Unit]
Description={app_name} Service
After=network.target

[Service]
ExecStart={entry}
Type=simple
Restart=on-failure

[Install]
WantedBy=multi-user.target
"""
        out = _service_file(app_name)
        out.write_text(template)
        os.system(f"ln -sf {out} /etc/systemd/system/{app_name}.service")


@registry.command()
def register(app: str,
             port: int = typer.Option(...),
             debug: bool = typer.Option(False, "--debug", "-d")):
    if not _ensure_admin():
        typer.echo(typer.style(
            "You need admin privileges to register a service.",
            fg=typer.colors.RED, bold=True
        ))
        raise typer.Exit(1)

    create_service(app, port, debug)

    if os.name == "nt":
        f = _service_file(app)
        os.system(f"{sys.executable} {f} install")
        os.system(f"{sys.executable} {f} start")
    else:
        os.system("systemctl daemon-reload")
        os.system(f"systemctl enable {app}")
        os.system(f"systemctl start {app}")

    typer.echo(typer.style(f"Service {app} registered.", fg=typer.colors.GREEN, bold=True))


@registry.command()
def start(app: str):
    if os.name == "nt":
        f = _service_file(app)
        os.system(f"{sys.executable} {f} start")
    else:
        os.system(f"systemctl start {app}")

    typer.echo(typer.style(f"Service {app} started.", fg=typer.colors.GREEN, bold=True))


@registry.command()
def stop(app: str):
    if os.name == "nt":
        f = _service_file(app)
        os.system(f"{sys.executable} {f} stop")
    else:
        os.system(f"systemctl stop {app}")

    typer.echo(typer.style(f"Service {app} stopped.", fg=typer.colors.YELLOW, bold=True))


@registry.command()
def remove(app: str):
    if not _ensure_admin():
        typer.echo(typer.style(
            "You need admin privileges to remove a service.",
            fg=typer.colors.RED, bold=True
        ))
        raise typer.Exit(1)

    if os.name == "nt":
        f = _service_file(app)
        os.system(f"{sys.executable} {f} stop")
        os.system(f"{sys.executable} {f} remove")
        f.unlink(missing_ok=True)
    else:
        os.system(f"systemctl stop {app}")
        os.system(f"systemctl disable {app}")
        (_service_file(app)).unlink(missing_ok=True)
        os.system("systemctl daemon-reload")

    typer.echo(typer.style(f"Service {app} removed.", fg=typer.colors.RED, bold=True))


def registry_entry(app: typer.Typer):
    app.add_typer(registry, name="registry")
