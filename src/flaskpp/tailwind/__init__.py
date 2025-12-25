from flask import Flask
from pathlib import Path
from tqdm import tqdm
import os, platform, typer, requests, subprocess

home = Path(__file__).parent.resolve()
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


def _tailwind_cmd() -> str:
    tw = "tailwind"
    if os.name == "nt":
        tw += ".exe"

    executable = home / tw
    if not executable.exists():
        raise TailwindError("Missing tailwind cli executable.")

    return str(executable)


def generate_tailwind_css(app: Flask):
    out =  (home.parent / "app" / "static" / "css" / "tailwind.css")

    if not out.exists():
        result = subprocess.run(
            [_tailwind_cmd(),
             "-i", str(out.parent / "tailwind_raw.css"),
             "-o", str(out), "--minify"],
            cwd=home.parent
        )
        if result.returncode != 0:
            raise TailwindError(f"Failed to generate {out}")

    root = Path(app.root_path).resolve()

    for d in root.rglob("static/css"):
        in_file = d / "tailwind_raw.css"
        if not in_file.exists():
            continue

        result = subprocess.run(
            [_tailwind_cmd(),
             "-i", str(in_file),
             "-o", str(d / "tailwind.css"), "--minify"],
            cwd=d
        )
        if result.returncode != 0:
            raise TailwindError(f"Failed to generate {d / 'tailwind.css'}")


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
