from pathlib import Path
from tqdm import tqdm
import os, platform, requests, typer, subprocess

from flaskpp.exceptions import NodeError

home = Path(__file__).parent
node_standalone = {
    "linux": "https://nodejs.org/dist/v24.11.1/node-v24.11.1-linux-{architecture}.tar.xz",
    "windows": "https://nodejs.org/dist/v24.11.1/node-v24.11.1-win-{architecture}.zip",
    "darwin": "https://nodejs.org/dist/v24.12.0/node-v24.12.0-darwin-{architecture}.tar.gz"
}


def _sys_node() -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["npm", "--version"],
            capture_output=True,
            text=True
        )
    except FileNotFoundError:
        return False, ""
    return result.returncode == 0, result.stdout or ""


def _get_node_data():
    selector = platform.system().lower()

    machine = platform.machine().lower()
    arch = "x64" if machine == "x86_64" or machine == "amd64" else "arm64"

    return node_standalone[selector].format(architecture=arch), selector


def _node_cmd(cmd: str) -> str:
    node = home / "node"
    if not node.exists():
        if not _sys_node()[0]:
            raise NodeError("Missing node installation / integration... Try running 'fpp init' inside a project directory.")
        return cmd

    if os.name == "nt":
        return str(node / f"{cmd}.cmd")
    return str(node / "bin" / cmd)


def _node_env() -> dict:
    env = os.environ.copy()
    if os.name != "nt":
        node_bin = str(home / "node" / "bin")
        env["PATH"] = node_bin + os.pathsep + env.get("PATH", "")
    else:
        node_dir = str(home / "node")
        env["PATH"] = node_dir + os.pathsep + env.get("PATH", "")
    return env


def load_node():
    sys_node = _sys_node()
    if sys_node[0]:
        typer.echo(f"Node.js version {sys_node[1]} is already installed... Skipping integration.")
        return

    data = _get_node_data()
    file_type = "zip" if data[1] == "windows" else (
        "tar.xz" if data[1] == "linux" else "tar.gz")
    dest = home / f"node.{file_type}"
    bin_folder = home / "node"

    if bin_folder.exists():
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
        raise NodeError("Failed to download standalone node bundle.")

    typer.echo(typer.style(f"Extracting node.{file_type}...", bold=True))

    if file_type == "zip":
        import zipfile
        with zipfile.ZipFile(dest, "r") as f:
            f.extractall(home)
    else:
        import tarfile
        with tarfile.open(dest, "r") as f:
            f.extractall(home)

    extracted_folder = home / data[0].split("/")[-1].removesuffix(f".{file_type}")
    extracted_folder.rename(bin_folder)

    dest.unlink()
