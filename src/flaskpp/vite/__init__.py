from flask import Blueprint, Response, send_from_directory
from pathlib import Path
from tqdm import tqdm
from dataclasses import dataclass
from typing import Optional, List, Dict
from threading import Thread
import os, platform, requests, typer, subprocess, json, time

from flaskpp.utils import enabled


@dataclass
class ManifestChunk:
    src: Optional[str] = None
    file: str = ""
    css: Optional[List[str]] = None
    assets: Optional[List[str]] = None
    isEntry: bool = False
    name: Optional[str] = None
    isDynamicEntry: bool = False
    imports: Optional[List[str]] = None
    dynamicImports: Optional[List[str]] = None

Manifest = Dict[str, ManifestChunk]

home = Path(__file__).parent
node_standalone = {
    "linux": "https://nodejs.org/dist/v24.11.1/node-v24.11.1-linux-{architecture}.tar.xz",
    "win": "https://nodejs.org/dist/v24.11.1/node-v24.11.1-win-{architecture}.zip"
}

vite_conf = """
import {{ defineConfig }} from 'vite'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({{
  root: "{root}",
  publicDir: "{public}",
  build: {{
    manifest: true,
    outDir: "{out}",
  }},
  plugins: [
    tailwindcss(),
  ],
}})
"""


def _get_node_data():
    selector = "win" if os.name == "nt" else "linux"

    machine = platform.machine().lower()
    arch = "x64" if machine == "x86_64" or machine == "amd64" else "arm64"

    return node_standalone[selector].format(architecture=arch), selector


def _node_cmd(cmd: str) -> str:
    if os.name == "nt":
        return str(home / "node" / f"{cmd}.cmd")
    return str(home / "node" / "bin" / cmd)


def load_node():
    data = _get_node_data()
    file_type = "zip" if data[1] == "win" else "tar.xz"
    dest = home / f"node.{file_type}"

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
        raise ViteError("Failed to download standalone node bundle.")

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
    bin_folder = home / "node"
    extracted_folder.rename(bin_folder)

    dest.unlink()


def setup_vite():
    typer.echo(typer.style("Setting up vite...", bold=True))
    result = subprocess.run(
        [_node_cmd("npm"), "install"],
        cwd=home
    )
    if result.returncode != 0:
        typer.echo(typer.style("Failed to setup vite.", fg=typer.colors.RED, bold=True))
        return

    root = (Path(os.getcwd()) / "vite").resolve()
    root.mkdir(exist_ok=True)
    public = root / "public"
    public.mkdir(exist_ok=True)
    (home / "vite.config.js").write_text(vite_conf.format(
        root=str(root),
        public=str(public),
        out=str(root / "dist")
    ))

    typer.echo(typer.style("Vite successfully prepared.", fg=typer.colors.GREEN, bold=True))


def load_manifest() -> Manifest:
    manifest_file = Path("vite/dist/.vite/manifest.json")
    if not manifest_file.exists():
        raise ViteError("Failed to load Vites manifest.json")
    raw = json.loads(manifest_file.read_text())
    manifest: Manifest = {}

    for key, data in raw.items():
        manifest[key] = ManifestChunk(**data)

    return manifest


def resolve_entry(manifest: Manifest, entry: str):
    if entry not in manifest:
        raise ViteError(f"'{entry}' not found in Vite manifest.")

    js_files = set()
    css_files = set()

    visited = set()
    def collect(chunk_name: str):
        chunk = manifest.get(chunk_name)
        if not chunk:
            return
        if chunk in visited:
            return
        visited.add(chunk)

        js_files.add(chunk.file)

        if chunk.css:
            css_files.update(chunk.css)

        if chunk.imports:
            for dep in chunk.imports:
                collect(dep)

    collect(entry)
    return list(js_files), list(css_files)


class Frontend(Blueprint):
    def __init__(self):
        super().__init__("vite", __name__)
        self.url_prefix = "/vite"
        self.route("/<path:path>")(self.serve)

        if enabled("DEBUG"):
            self.session = requests.Session()
            self.port = int(os.getenv("SERVER_PORT", "5000")) + 1000
            self.server = subprocess.Popen(
                [_node_cmd("npm"), "run", "dev", "--port", str(self.port)],
                cwd=home
            )
        else:
            self.build = subprocess.Popen(
                [_node_cmd("npm"), "run", "build"],
                cwd=home
            )
            self.manifest = None
            self.loader = Thread(target=self._load_manifest)
            self.loader.start()

    def _load_manifest(self):
        if not self.built:
            timer = 0
            while not self.built:
                if timer >= 100:
                    raise ViteError("Vite was not built successfully.")
                time.sleep(0.1)
                timer += 1
        self.manifest = load_manifest()

    def vite(self, entry: str):
        if enabled("DEBUG"):
            return f'<script type="module" src="/vite/{entry}"></script>'

        js, css = resolve_entry(self.manifest, entry)

        tags = []

        for file in css:
            tags.append(f'<link rel="stylesheet" href="/vite/{file}">')

        for file in js:
            tags.append(f'<script type="module" src="/vite/{file}"></script>')

        return "\n".join(tags)

    def serve(self, path) -> Response:
        if not enabled("DEBUG"):
            dist = Path("vite/dist")

            if self.built and not dist.exists():
                raise ViteError("Missing vite/dist directory.")
            elif self.loader.is_alive():
                 self.loader.join()
            else:
                raise ViteError("There was an error while building vite.")

            return send_from_directory(dist.resolve(), path)

        if not self.server or self.server.poll() is not None:
            raise ViteError("Frontend server is not running.")
        upstream = self.session.get(f"http://localhost:{self.port}/{path}")
        return Response(upstream.content, upstream.status_code)

    @property
    def built(self) -> bool:
        return not enabled("DEBUG") and self.build.returncode == 0


class ViteError(Exception):
    pass
