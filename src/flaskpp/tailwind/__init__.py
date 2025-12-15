from pathlib import Path
from tqdm import tqdm
import os, platform, typer, requests, subprocess

home = Path(__file__).parent
tailwind_cli = {
    "linux": "https://github.com/tailwindlabs/tailwindcss/releases/download/v4.1.17/tailwindcss-linux-{architecture}",
    "win": "https://github.com/tailwindlabs/tailwindcss/releases/download/v4.1.17/tailwindcss-windows-x64.exe"
}


def _get_cli_data():
    selector = "win" if os.name == "nt" else "linux"

    machine = platform.machine().lower()
    arch = "x64" if machine == "x86_64" or machine == "amd64" else "arm64"

    if selector == "linux":
        return tailwind_cli[selector].format(architecture=arch), selector
    return tailwind_cli[selector], selector


def _tailwind_cmd():
    if os.name == "nt":
        return str(home / "tailwind.exe")
    return str(home / "tailwind")


def generate_tailwind_css():
    app = (home.parent / "app").resolve()
    css =  app / "static" / "css"

    if not os.getcwd() in str(app):
        out = css / "tailwind_fpp.css"
        if not out.exists():
            result = subprocess.run(
                [_tailwind_cmd(),
                 "-i", str(css / "tailwind_raw.css"),
                 "-o", str(out), "--minify",
                 "--cwd", str(app)],
            )
            if result.returncode != 0:
                raise TailwindError("Failed to generate tailwind_fpp.css")

    result = subprocess.run(
        [_tailwind_cmd(),
         "-i", str(css / "tailwind_raw.css"),
         "-o", str(css / "tailwind.css"), "--minify",
         "--cwd", os.getcwd()],
    )
    if result.returncode != 0:
        raise TailwindError("Failed to generate tailwind.css")


def setup_tailwind():
    data = _get_cli_data()
    file_type = ".exe" if data[1] == "win" else ""
    dest = home / f"tailwind{file_type}"

    if dest.exists():
        return

    typer.echo(typer.style(f"Downloading {data[0]}...", bold=True))
    with requests.get(data[0], stream=True) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        with open(dest, "wb") as f, tqdm(
                total=total, unit="B", unit_scale=True, desc=str(dest)
        ) as bar:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
                bar.update(len(chunk))

    if not dest.exists():
        raise TailwindError("Failed to load tailwind cli.")

    if os.name != "nt":
        os.system(f"chmod +x {str(dest)}")

    typer.echo(typer.style(f"Tailwind successfully setup.", fg=typer.colors.GREEN, bold=True))


class TailwindError(Exception):
    pass
