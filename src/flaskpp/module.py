from flask import Blueprint, Response, render_template, url_for, request, send_from_directory, redirect
from werkzeug.exceptions import NotFound
from markupsafe import Markup
from importlib import import_module
from pathlib import Path
from typing import Callable, TYPE_CHECKING
import json, typer, subprocess, sys

from flaskpp.utils import (required_arg_count, require_extensions,
                           enabled, check_required_version)
from flaskpp.utils.debugger import log
from flaskpp.exceptions import ModuleError, ManifestError, EventHookException

if TYPE_CHECKING:
    from flaskpp import FlaskPP, Module
    from configparser import ConfigParser


class ModuleVersion(tuple):
    def __new__(cls, major: int, minor: int | None = None, patch: int | None = None):
        minor = 0 if minor is None else minor
        patch = 0 if patch is None else patch
        return super().__new__(cls, (major, minor, patch))

    @property
    def length(self) -> int:
        if self[2] != 0:
            return 3
        if self[1] != 0:
            return 2
        return 1

    def __str__(self) -> str:
        return f"v{'.'.join(map(str, self[:self.length]))}"


class Module(Blueprint):
    def __init__(self, file: str, import_name: str,
                 extends: "Module" = None, required_extensions: list = None,
                 init_routes_on_enable: bool = True, allowed_for_home: bool = True,
                 allow_frontend_engine: bool = True):

        if not "modules." in import_name:
            raise ModuleError("Modules have to be created inside the 'modules' package.")

        self.module_name = import_name.split(".")[-1]
        self.import_name = import_name
        self.root_path = Path(file).parent
        manifest = self.root_path / "manifest.json"
        self.info = self._load_manifest(manifest)
        self.is_base = self.info["type"] == "base"
        self.required_extensions = required_extensions or []
        self.context = {
            "NAME": self.info["id"],
        }
        self._handlers = {}
        self.home = False

        if extends and self.is_base:
            raise ModuleError("Base modules cannot extend other modules.")
        elif extends and not extends.is_base:
            raise ModuleError("Modules can only extend base modules.")

        self.base = extends
        self.parent = None

        if extends:
            self.required_extensions.extend(extends.required_extensions or [])

        self.enable = require_extensions(*self.required_extensions)(self._enable)
        self._on_enable = None
        self._init_routes = init_routes_on_enable
        self._allow_home = allowed_for_home
        self._allow_vite = allow_frontend_engine

        super().__init__(
            self.info["id"],
            import_name,
            static_folder=(Path(self.root_path) / "static"),
            url_prefix="/base" if self.is_base else None
        )

    def __repr__(self):
        return f"<{self.module_name} {self.version}> {self.info.get('description', '')}"

    def _enable(self, app: "FlaskPP", home: bool):
        if self.is_base:
            raise ModuleError(f"[{self.module_name}] Base modules are not allowed to be registered.")

        self.check_module_requirements()

        if home and not self._allow_home:
            raise ModuleError(f"[{self.module_name}] Module is not allowed to be registered as home module.")
        elif home:
            self.static_url_path = "/static"
            app.url_prefix = "/app"
            self.home = True
        else:
            self.url_prefix = f"/{self.name}"
            self.static_url_path = f"/{self.name}/static"

        if self.base and self.base.parent:
            raise ModuleError(
                f"[{self.module_name}] Base module '{self.base.module_name}' is already extended by "
                f"module '{self.base.parent.module_name}'."
            )
        elif self.base:
            self.base.check_module_requirements()
            self.base.init_handling()
            self.base.init_routes()
            self.register_blueprint(self.base)

            if self.home:
                app.errorhandler(NotFound)(self._not_found)
            else:
                self.errorhandler(NotFound)(self._not_found)

            app.context[self.base.name.upper()] = self.name
            self.base.parent = self

        self.init_handling()

        if self._init_routes:
            self.init_routes()

        if enabled("FRONTEND_ENGINE") and self._allow_vite:
            from flaskpp.fpp_node.fpp_vite import Frontend
            engine = Frontend(self)
            self.context["vite"] = engine.vite
            self.frontend_engine = engine
            app.on_shutdown(engine.shutdown)

        if self.base:
            mod_tailwind = lambda: Markup(
                f"<link rel='stylesheet' href='{self.url_for('static', filename='css/tailwind.css')}'>\n"
                f"<link rel='stylesheet' href='{self.url_for(f'{self.base.name}.static', filename='css/tailwind.css')}'>"
            )
            context_processor = lambda: dict(
                **(self.base.context | self.context),
                tailwind=mod_tailwind()
            )
        else:
            mod_tailwind = lambda: Markup(
                f"<link rel='stylesheet' href='{self.url_for('static', filename='css/tailwind.css')}'>"
            )
            context_processor = lambda: dict(
                **self.context,
                tailwind=mod_tailwind()
            )

        if self.home:
            app.context_processor(context_processor)
        else:
            self.context_processor(context_processor)

        if enabled("FPP_PROCESSING") and not self.home:
            app.context[f"{self.name}_tailwind"] = mod_tailwind

        if self._on_enable is not None:
            self._on_enable(app)

        app.register_blueprint(self)

    def _load_manifest(self, manifest: Path) -> dict:
        try:
            module_data = basic_checked_data(manifest)
        except (FileNotFoundError, ManifestError, json.JSONDecodeError) as e:
            raise ModuleError(f"[{self.module_name}] Failed to load manifest: {e}")

        if not "id" in module_data:
            log("warn", f"[{self.module_name}] Missing id; Using package name as id instead.")
            module_data["id"] = self.module_name

        if not "name" in module_data:
            log("warn", f"[{self.module_name}] Module name not defined, leaving empty.")
        else:
            self.module_name = module_data["name"]

        if not "description" in module_data:
            log("warn", f"[{self.module_name}] Missing description.")

        if not "author" in module_data:
            log("warn", f"[{self.module_name}] Author not defined.")

        if not "requires" in module_data:
            log("warn", f"[{self.module_name}] Requirements not defined.")

        else:
            if not enabled("IN_EXECUTION"):
                return module_data

            requirements = module_data["requires"]

            if not "fpp" in requirements:
                log("warn", f"[{self.module_name}] Required Flask++ version of not defined.")
            else:
                fulfilled = check_required_version(requirements["fpp"])
                if not fulfilled:
                    raise ModuleError(
                        f"[{self.module_name}] Module requires Flask++ version {requirements['fpp']}."
                    )

        return module_data

    def check_module_requirements(self):
        if not "requires" in self.info:
            return

        requirements = self.info["requires"]
        if "modules" in requirements:
            from flaskpp.modules import installed_modules, import_base
            modules = installed_modules(Path(self.root_path).parent, False)
            requirement = requirements["modules"]

            if isinstance(requirement, list):
                new = {}
                for r in requirement:
                    if not isinstance(r, str):
                        raise ManifestError(f"[{self.module_name}] Invalid module requirement '{r}'.")
                    r = r.split("@")
                    if len(r) == 2:
                        m, v = r
                    else:
                        m = r[0]
                        v = "*"
                    new[m] = v
                requirement = new

            if not isinstance(requirement, dict):
                raise ManifestError(f"[{self.module_name}] Invalid modules requirement type: {type(requirement)}")

            requirement_copy = requirement.copy()

            for module in modules:
                m, v, _ = module
                if m not in requirement:
                    continue

                if not enabled(m):
                    continue

                if check_required_version(requirement.get(m, "*"), "module", v):
                    requirement_copy.pop(m)

            requirement = requirement_copy.copy()

            for m, v in requirement.items():
                base = import_base(m)
                if base and check_required_version(v, "module", base.version):
                    requirement_copy.pop(m)

            if len(requirement_copy) > 0:
                raise ModuleError(
                    f"[{self.module_name}] Missing or mismatching module requirements: {[m for m in requirement_copy]}"
                )

    def _not_found(self, error: NotFound) -> Response:
        if "static" in request.path:
            filename = request.path.replace("/static/", "::").split("::")[-1]
            return send_from_directory(Path(self.base.root_path) / "static", filename)

        if request.path == "/" or "/base/base/base" in request.path:
            from flaskpp.app.utils.processing import get_handler
            return get_handler("handle_app_error")(error)

        prefix = self.url_prefix if self.url_prefix else ""
        return redirect(f"{prefix}/base{request.path}")

    def extract(self):
        from flaskpp.cli import cwd
        extract_path = Path(self.root_path) / "extract"
        base_extract_path = Path(self.base.root_path) / "extract" if self.base else None

        def for_dir(path, name):
            module_name = self.base.module_name if path == base_extract_path else self.module_name

            for file in (path / name).rglob("*"):
                if not file.is_file():
                    continue

                rel = file.relative_to(path)
                dst = cwd / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                if dst.exists():
                    typer.echo(typer.style(
                        f"[{module_name}] Could not extract '{'/'.join(rel.parts)}': "
                         "File already exists.", fg=typer.colors.YELLOW
                    ))
                    continue

                typer.echo(f"[{module_name}] Extracting '{'/'.join(rel.parts)}'.")

                dst.write_bytes(
                    file.read_bytes()
                )

        for_dir(extract_path, "static")
        for_dir(extract_path, "templates")

        if base_extract_path:
            for_dir(base_extract_path, "static")
            for_dir(base_extract_path, "templates")

        typer.echo(typer.style(
            f"[{self.module_name}] Finished extracting modules extract files to main app.",
            fg=typer.colors.GREEN, bold=True
        ))

    def install_packages(self):
        if not "requires" in self.info:
            return

        requirements = self.info["requires"]
        if not "packages" in requirements:
            return

        packages = requirements["packages"]
        if not isinstance(packages, list):
            typer.echo(typer.style(
                f"[{self.module_name}] Invalid packages requirement type: {type(packages)}",
                fg=typer.colors.YELLOW, bold=True
            ))
            return

        base_packages = []
        if self.base and "requires" in self.base.info and "packages" in self.base.info["requires"]:
            base_packages = self.base.info["requires"]["packages"]
            if isinstance(base_packages, list):
                packages = list(set(base_packages) | set(packages))
            else:
                typer.echo(typer.style(
                    f"[{self.base.module_name}] Invalid packages requirement type: {type(base_packages)}",
                    fg=typer.colors.YELLOW, bold=True
                ))

        for package in packages:
            module_name = self.base.module_name if package in base_packages else self.module_name

            typer.echo(f"[{module_name}] Installing required package '{package}'...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", package],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                typer.echo(typer.style(
                    f"[{module_name}] Failed to install package '{package}': {result.stderr}",
                    fg=typer.colors.RED, bold=True
                ))

        typer.echo(typer.style(
            f"[{self.module_name}] Finished installing required packages.",
            fg=typer.colors.GREEN, bold=True
        ))

    def setup_config(self, config: "ConfigParser", config_file_exists: bool = False):
        if self.is_base:
            return

        try:
            cfg = import_module(f"{self.import_name}.config")
            module_config = getattr(cfg, "module_config", None)
            if not module_config:
                raise ImportError()

            if self.base:
                try:
                    base_cfg = import_module(f"{self.base.import_name}.config")
                    base_module_config = getattr(base_cfg, "module_config", None)
                    if not base_module_config:
                        raise ImportError()
                    extend = base_module_config() or {}
                except (ModuleNotFoundError, ImportError, TypeError):
                    extend = {}
            else:
                extend = {}

            try:
                main = module_config() or {}
            except TypeError:
                main = {}

            combined = {**extend, **main}
            if not combined:
                return

            from flaskpp.utils.setup import setup_config
            setup_config(config, combined, config_file_exists)

        except (ModuleNotFoundError, ImportError):
            return

    def init_models(self):
        if self.is_base or "sqlalchemy" not in self.required_extensions:
            return

        try:
            data = import_module(f"{self.import_name}.data")
            init_models = getattr(data, "init_models", None)
            if not init_models:
                raise ImportError("Missing init function in data.")
            init_models(self)
        except (ModuleNotFoundError, ImportError, TypeError) as e:
            log("warn", f"[{self.module_name}] Failed to initialize database models: {e}")

    def init_handling(self):
        try:
            handling = import_module(f"{self.import_name}.handling")
            init_handling = getattr(handling, "init_handling", None)
            if not init_handling:
                raise ImportError("Missing init function in handling.")
            init_handling(self)
        except (ModuleNotFoundError, ImportError, TypeError) as e:
            log("warn", f"[{self.module_name}] Failed to initialize handling: {e}")

    def init_routes(self):
        try:
            routes = import_module(f"{self.import_name}.routes")
            init = getattr(routes, "init_routes", None)
            if not init:
                raise ImportError("Missing init function in routes.")
            init(self)
        except (ModuleNotFoundError, ImportError, TypeError) as e:
            log("warn", f"[{self.module_name}] Failed to register routes: {e}")

    def wrap_message(self, message: str) -> str:
        domain = self.context.get("DOMAIN")
        if not domain:
            return message
        return f"{message}@{domain}"

    def t(self, message: str) -> str:
        from flaskpp.app.utils.translating import t
        return t(self.wrap_message(message), False)

    def tn(self, singular: str, plural: str, n: int) -> str:
        from flaskpp.app.utils.translating import tn
        return tn(self.wrap_message(singular), plural, n, False)

    def handler(self, name: str) -> Callable:
        def decorator(func):
            def wrapper(*args):
                return func(self, *args)
            self._handlers[name] = wrapper
            return wrapper
        return decorator

    def handle_request(self, handler_name: str) -> Callable:
        def no_handler(*_, **__):
            raise NotImplementedError(f"[{self.module_name}] Module does not have a handler called '{handler_name}'.")
        return self._handlers.get(handler_name, no_handler)

    def render_template(self, template: str, **context) -> str:
        if self.is_base and not self.parent:
            raise ModuleError(f"[{self.module_name}] Base modules require a parent module to render templates.")
        render_name = template if self.ref.home else f"{self.ref.name}/{template}"
        return render_template(render_name, **context)

    def url_for(self, endpoint: str, **kwargs) -> str:
        if self.is_base and not self.parent:
            raise ModuleError(f"[{self.module_name}] Base modules require a parent module to calculate urls.")
        elif self.is_base:
            return url_for(f"{self.ref.name}.{self.name}.{endpoint}", **kwargs)
        return url_for(f"{self.name}.{endpoint}", **kwargs)

    def on_enable(self, fn: Callable) -> Callable:
        if self.is_base:
            raise ModuleError(f"[{self.module_name}] Base modules cannot have on_enable hooks.")

        if required_arg_count(fn) != 1:
            raise EventHookException(
                f"[{self.module_name}] on_enable hooks must take exactly one non optional argument: 'app'."
            )

        self._on_enable = fn
        return fn

    @property
    def version(self) -> ModuleVersion:
        return valid_version(self.info.get("version", ""))

    @property
    def ref(self) -> "Module":
        ref = self
        if self.is_base and self.parent:
            ref = self.parent
        return ref


def version_check(v: str) -> tuple[bool, str]:
    version_str = v.lower().strip()
    if not version_str:
        return False, "Module version not defined."

    first_char_invalid = False
    try:
        int(version_str[0])
    except ValueError:
        first_char_invalid = True

    if  first_char_invalid \
            or (" " in version_str and not (
            version_str.endswith("alpha")
            or version_str.endswith("beta")
            or version_str.endswith("rc")
    )):
        return False, "Invalid version string format."

    try:
        v_numbers = version_str.split(" ")[0].split(".")
        if len(v_numbers) > 3:
            return False, "Too many version numbers."

        for v_number in v_numbers:
            int(v_number)
    except ValueError:
        return False, "Invalid version numbers."

    return True, version_str


def basic_checked_data(manifest: Path) -> dict:
    if not manifest.exists():
        raise FileNotFoundError("Missing manifest.")

    try:
        module_data = json.loads(manifest.read_text())
    except json.decoder.JSONDecodeError:
        raise ManifestError("Invalid manifest format.")

    if not "version" in module_data:
        raise ManifestError("Module version not defined.")

    if not "type" in module_data:
        raise ManifestError("Module type not defined.")
    elif not module_data["type"] in ["base", "default"]:
        raise ManifestError(f"Invalid module type: {module_data['type']}")

    return module_data


def valid_version(version: str) -> ModuleVersion:
    check = version_check(version)
    if not check[0]:
        raise ManifestError(check[1])

    return ModuleVersion(*map(int, check[1].split(".")))
