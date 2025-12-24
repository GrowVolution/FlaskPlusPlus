from pathlib import Path
import typer, os, sys, ctypes, subprocess, shlex

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


def service_file(app: str):
    return service_path / (f"{app}.py" if os.name == "nt" else f"{app}.service")


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
        servicemanager.LogInfoMsg("{app_name} Service stopped.")

    def SvcDoRun(self):
        servicemanager.LogInfoMsg("{app_name} Service started.")
        self.main_loop()

    def main_loop(self):
        proc = subprocess.Popen(
            [{entry_list}],
            cwd=r"{str(home)}"
        )
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
        if target.is_symlink() or target.exists():
            target.unlink()
        target.symlink_to(out)


@registry.command()
def register(app: str = typer.Option(..., "--app", "-a"),
             port: int = typer.Option(5000, "--port", "-p"),
             debug: bool = typer.Option(False, "--debug", "-d")):
    if not _ensure_admin():
        typer.echo(typer.style(
            "You need admin privileges to register a service.",
            fg=typer.colors.RED, bold=True
        ))
        raise typer.Exit(1)

    if not (app and (home / "app_configs" / f"{app}.conf").exists()):
        typer.echo(typer.style(
            "You must specify a valid app to register it.",
            fg=typer.colors.RED, bold=True
        ))
        raise typer.Exit(1)

    create_service(app, port, debug)

    if os.name == "nt":
        f = service_file(app)
        subprocess.run([sys.executable, str(f), "install"], check=False)
        subprocess.run([sys.executable, str(f), "start"], check=False)
    else:
        subprocess.run(["systemctl", "daemon-reload"], check=False)
        subprocess.run(["systemctl", "enable", app], check=False)
        subprocess.run(["systemctl", "start", app], check=False)

    typer.echo(typer.style(f"Service {app} registered.", fg=typer.colors.GREEN, bold=True))


@registry.command()
def start(app: str):
    if os.name == "nt":
        f = service_file(app)
        subprocess.run([sys.executable, str(f), "start"], check=False)
    else:
        subprocess.run(["systemctl", "start", app], check=False)

    typer.echo(typer.style(f"Service {app} started.", fg=typer.colors.GREEN, bold=True))


@registry.command()
def stop(app: str):
    if os.name == "nt":
        f = service_file(app)
        subprocess.run([sys.executable, str(f), "stop"], check=False)
    else:
        subprocess.run(["systemctl", "stop", app], check=False)

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
        f = service_file(app)
        subprocess.run([sys.executable, str(f), "stop"], check=False)
        subprocess.run([sys.executable, str(f), "remove"], check=False)
        f.unlink(missing_ok=True)
    else:
        subprocess.run(["systemctl", "stop", app], check=False)
        subprocess.run(["systemctl", "disable", app], check=False)
        service_file(app).unlink(missing_ok=True)
        subprocess.run(["systemctl", "daemon-reload"], check=False)

    typer.echo(typer.style(f"Service {app} removed.", fg=typer.colors.RED, bold=True))


def registry_entry(app: typer.Typer):
    app.add_typer(registry, name="registry")
