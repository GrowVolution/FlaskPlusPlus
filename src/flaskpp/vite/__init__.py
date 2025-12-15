from flask import Blueprint, Response, send_from_directory
from werkzeug.datastructures import Headers
from markupsafe import Markup
from pathlib import Path
from tqdm import tqdm
from dataclasses import dataclass
from typing import Optional, List, Dict
from threading import Thread
import os, platform, requests, typer, subprocess, json, time, re

from flaskpp.utils import enabled, is_port_free


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

package_json = """
{
  "name": "fpp-vite",
  "version": "0.0.2",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "devDependencies": {
    "vite": "^7.2.4"
  },
  "dependencies": {
    "@tailwindcss/vite": "^4.1.17",
    "tailwindcss": "^4.1.17"
  }
}
"""

vite_conf = """
import {{ defineConfig }} from "vite"
import tailwindcss from "@tailwindcss/vite"

export default defineConfig({{
  root: "{root}",
  build: {{
    manifest: true,
    rollupOptions: {{
      input: "{entry_point}",
    }},
  }},
  plugins: [
    tailwindcss(),
  ],
}})
"""

vite_main = """
const _ = window.FPP?._ ?? (async msg => msg)

const el = document.querySelector('#main')
if (el) {
  (async () => {
    el.innerHTML = `
      <div class="flex flex-col min-h-[100dvh] items-center justify-center px-6 py-8">
        <h2 class="text-2xl font-semibold">${await _("Welcome!")}</h2>
        <p class="mt-2">${await _("This is your wonderful new app.")}</p>
      </div>
    `
  })()
}
"""

_ports_in_use = []


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
    extracted_folder.rename(bin_folder)

    dest.unlink()


def prepare_vite():
    typer.echo(typer.style("Setting up vite...", bold=True))
    (home / "package.json").write_text(package_json)

    result = subprocess.run(
        [_node_cmd("npm"), "install"],
        cwd=home
    )
    if result.returncode != 0:
        typer.echo(typer.style("Failed to setup vite.", fg=typer.colors.RED, bold=True))
        return

    typer.echo(typer.style("Vite successfully prepared.", fg=typer.colors.GREEN, bold=True))


def load_manifest(dist: Path) -> Manifest:
    manifest_file = dist / ".vite" / "manifest.json"
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
        if chunk_name in visited:
            return

        chunk = manifest.get(chunk_name)
        if not chunk:
            return
        visited.add(chunk_name)

        js_files.add(chunk.file)

        if chunk.css:
            css_files.update(chunk.css)

        if chunk.imports:
            for dep in chunk.imports:
                collect(dep)

    collect(entry)
    return list(js_files), list(css_files)


class Frontend(Blueprint):
    from flaskpp import FlaskPP, Module
    def __init__(self, parent: FlaskPP | Module):
        super().__init__(f"{parent.name}_vite", parent.import_name)
        prefix = "/vite"
        self.url_prefix = prefix
        self.route("/<path:path>")(self.serve)
        self.prefix = f"{parent.url_prefix}{prefix}" if hasattr(parent, "url_prefix") and parent.url_prefix is not None else prefix

        root = (Path(parent.root_path) / "vite").resolve()
        root.mkdir(exist_ok=True)
        public = root / "public"
        public.mkdir(exist_ok=True)
        main = root / "main.js"
        safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", parent.name)
        conf_name = f"vite.config.{safe_name}.js"
        (home / conf_name).write_text(vite_conf.format(
            root=str(root),
            entry_point=str(main)
        ))
        conf_params = ["--config", conf_name]
        if not main.exists():
            main.write_text(vite_main)

        if enabled("DEBUG_MODE"):
            self.session = requests.Session()
            self.port = int(os.getenv("SERVER_PORT", "5000")) if len(_ports_in_use) == 0 else _ports_in_use[-1]
            self.port += 100
            while not is_port_free(self.port):
                self.port += 100
            _ports_in_use.append(self.port)

            self.server = subprocess.Popen(
                [_node_cmd("npm"), "run", "dev", "--", "--port", str(self.port), *conf_params],
                cwd=home
            )
        else:
            self.build = subprocess.Popen(
                [_node_cmd("npm"), "run", "build", "--", *conf_params],
                cwd=home
            )
            self.dist = root / "dist"
            self.manifest = None
            self.loader = Thread(target=self._load_manifest)
            self.loader.start()

        parent.register_blueprint(self)

    def _load_manifest(self):
        self.build.wait()
        if self.build.returncode != 0:
            raise ViteError("Vite build process failed.")
        self.manifest = load_manifest(self.dist)

    def vite(self, entry: str):
        if enabled("DEBUG_MODE"):
            return Markup(f'<script type="module" src="{self.prefix}/{entry}"></script>')

        js, css = resolve_entry(self.manifest, entry)

        tags = []

        for file in css:
            tags.append(f'<link rel="stylesheet" href="{self.prefix}/{file}">')

        for file in js:
            tags.append(f'<script type="module" src="{self.prefix}/{file}"></script>')

        return Markup("\n".join(tags))

    def serve(self, path) -> Response:
        if not enabled("DEBUG_MODE"):
            if self.built and not self.dist.exists():
                raise ViteError("Missing vite/dist directory.")
            elif self.loader.is_alive():
                 self.loader.join()
            else:
                raise ViteError("There was an error while building vite.")

            return send_from_directory(self.dist.resolve(), path)

        if not self.server or self.server.poll() is not None:
            raise ViteError("Frontend server is not running.")
        upstream = self.session.get(f"http://localhost:{self.port}/{path}")
        response = Response(upstream.content, upstream.status_code)
        response.headers = Headers(upstream.headers)
        return response

    @property
    def built(self) -> bool:
        return not enabled("DEBUG_MODE") and self.build.returncode == 0


class ViteError(Exception):
    pass
