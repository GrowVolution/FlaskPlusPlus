from colorama import Fore, Style
from pathlib import Path
import os, sys, ctypes

file = Path(__file__).resolve()
service_path = file.parent.parent / "services"
service_path.mkdir(parents=True, exist_ok=True)


def _ensure_admin() -> bool:
    if os.name == "nt":
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    else:
        return os.geteuid() == 0


def create_service(app_name: str, port: int, debug: bool):
    enrtrypoint = f"{sys.executable} {str(file.parent.parent / "run.py")} --app {app_name} --port {port} {'--debug' if debug else ''}"

    if os.name == "nt":
        service_template = f"""
        import win32serviceutil, win32service, win32event, servicemanager, subprocess, time
        
        class AppService(win32serviceutil.ServiceFramework):
            _svc_name_ = f"{app_name} Service"
            _svc_display_name_ = f"{app_name} Background Service"
            _svc_description_ = (
                f"Runs the {app_name} backend as a persistent service."
            )

            def __init__(self, args):
                super().__init__(args)
                self.stop_event = win32event.CreateEvent(None, 0, 0, None)
                self.alive = True

            def SvcStop(self):
                self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
                win32event.SetEvent(self.stop_event)
                self.alive = False
                servicemanager.LogInfoMsg(f"{app_name} Service stopped.")

            def SvcDoRun(self):
                servicemanager.LogInfoMsg(f"{app_name} Service started.")
                self.main_loop()

            def main_loop(self):
                proc = subprocess.Popen(["cmd", "/C", f"{enrtrypoint}"])
                while self.alive:
                    if proc.poll() is not None:
                        raise RuntimeError("Service execution failed.")
                    time.sleep(1)
                proc.terminate()
                
        
        if __name__ == "__main__":
            win32serviceutil.HandleCommandLine(AppService)
        """
        service_file = service_path / f"{app_name}.py"
        with open(service_file, "w") as f:
            f.write(service_template)

    else:
        systemd_template = f"""
        [Unit]
        Description={app_name} Service
        After=network.target
        
        [Service]
        ExecStart={enrtrypoint}
        Type=simple
        Restart=on-failure
        
        [Install]
        WantedBy=multi-user.target
        """
        service_file = service_path / f"{app_name}.service"
        with open(service_file, "w") as f:
            f.write(systemd_template)
        os.system(f"ln -sf {service_file} /etc/systemd/system/{app_name}.service")


def register(app_name: str, port: int, debug: bool = False):
    if not _ensure_admin():
        print(f"{Fore.RED}{Style.BRIGHT}You need admin privileges to register a service.{Style.RESET_ALL}")
        exit(1)

    create_service(app_name, port, debug)

    if os.name == "nt":
        os.system(f"{sys.executable} {str(file)} install {app_name}")
        os.system(f"{sys.executable} {str(file)} start {app_name}")

    else:
        os.system("systemctl daemon-reload")
        os.system(f"systemctl start {app_name}")


if __name__ == "__main__":
    if not _ensure_admin():
        print(f"{Fore.RED}{Style.BRIGHT}You need admin privileges to use this util.{Style.RESET_ALL}")
        exit(1)

    if os.name == "nt":
        if len(sys.argv) > 2:
            service_file = service_path / f"{sys.argv[2]}.py"
            exit(os.system(f"{sys.executable} {str(service_file)} {sys.argv[1]}"))
        else:
            print(f"{Fore.RED}{Style.BRIGHT}Invalid syntax, use:{Style.RESET_ALL}")
            print(f"python {sys.argv[0]} [start/stopp] [app_name]")
            exit(1)

    else:
        if len(sys.argv) > 2:
            exit(os.system(f"systemctl {sys.argv[1]} {sys.argv[2]}"))
        else:
            print(f"{Fore.RED}{Style.BRIGHT}Invalid syntax, use:{Style.RESET_ALL}")
            print(f"python {sys.argv[0]} [start/stopp] [app_name]")
            exit(1)
