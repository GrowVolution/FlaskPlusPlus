from pathlib import Path
from tqdm import tqdm
import os, platform, requests, typer

home = Path(__file__).parent
node_standalone = {
    "linux": "https://nodejs.org/dist/v24.11.1/node-v24.11.1-linux-{architecture}.tar.xz",
    "win": "https://nodejs.org/dist/v24.11.1/node-v24.11.1-win-{architecture}.zip"
}


def _get_node_data():
    selector = "win" if os.name == "nt" else "linux"

    machine = platform.machine().lower()
    arch = "x64" if machine == "x86_64" or machine == "amd64" else "arm64"

    return node_standalone[selector].format(architecture=arch), selector


def _node_cmd(cmd: str) -> str:
    node = home / "node"
    if not node.exists():
        raise NodeError("Missing node directory.")

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
    data = _get_node_data()
    file_type = "zip" if data[1] == "win" else "tar.xz"
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


class NodeError(Exception):
    pass
