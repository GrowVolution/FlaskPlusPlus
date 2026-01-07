from flask import Blueprint, render_template, url_for
from markupsafe import Markup
from importlib import import_module
from pathlib import Path
from typing import Callable, TYPE_CHECKING
import json

from flaskpp.utils import (takes_arg, required_arg_count, require_extensions,
                           enabled, check_required_version)
from flaskpp.utils.debugger import log
from flaskpp.exceptions import ModuleError, ManifestError, EventHookException

if TYPE_CHECKING:
    from flaskpp import FlaskPP


class ModuleVersion(tuple):
    def __new__(cls, major: int, minor: int = None, patch: int = None):
        cls.length = 3

        if patch is None:
            cls.length -= 1
            patch = 0

        if minor is None:
            cls.length -= 1
            minor = 0

        return super().__new__(cls, (major, minor, patch))

    def __str__(self) -> str:
        return f"v{'.'.join(map(str, self[:self.length]))}"


class Module(Blueprint):
    def __init__(self, file: str, import_name: str, required_extensions: list = None,
                 init_routes_on_enable: bool = True):
        if not "modules." in import_name:
            raise ModuleError("Modules have to be created in the modules package.")

        self.module_name = import_name.split(".")[-1]
        self.import_name = import_name
        self.root_path = Path(file).parent
        manifest = self.root_path / "manifest.json"
        self.info = self._load_manifest(manifest)
        self.required_extensions = required_extensions or []
        self.context = {
            "NAME": self.info["id"],
        }
        self.home = False

        self.enable = require_extensions(*self.required_extensions)(self._enable)
        self._on_enable = None
        self._init_routes = init_routes_on_enable

        super().__init__(
            self.info["id"],
            import_name,
            static_folder=(Path(self.root_path) / "static")
        )

    def __repr__(self):
        return f"<{self.module_name} {self.version}> {self.info.get('description', '')}"

    def _enable(self, app: "FlaskPP", home: bool):
        if home:
            self.static_url_path = "/static"
            app.url_prefix = "/app"
            self.home = True
        else:
            self.url_prefix = f"/{self.name}"
            self.static_url_path = f"/{self.name}/static"

        if self._init_routes:
            self.init_routes()

        if "sqlalchemy" in self.required_extensions:
            try:
                data = import_module(f"{self.import_name}.data")
                init = getattr(data, "init_models", None)
                if not init:
                    raise ImportError("Missing init function in data.")
                init()
            except (ModuleNotFoundError, ImportError, TypeError) as e:
                log("warn", f"Failed to initialize database models for '{self.module_name}': {e}")

        if enabled("FRONTEND_ENGINE"):
            from flaskpp.fpp_node.fpp_vite import Frontend
            engine = Frontend(self)
            self.context["vite"] = engine.vite
            self.context["vite_prefix"] = engine.prefix
            self.frontend_engine = engine
            app.on_shutdown(engine.shutdown)

        self.context_processor(lambda: dict(
            **self.context,
            tailwind=Markup(f"<link rel='stylesheet' href='{url_for(f'{self.name}.static', filename='css/tailwind.css')}'>")
        ))

        if self._on_enable is not None:
            self._on_enable(app)

        app.register_blueprint(self)

    def _load_manifest(self, manifest: Path) -> dict:
        try:
            module_data = basic_checked_data(manifest)
        except (FileNotFoundError, ManifestError, json.JSONDecodeError) as e:
            raise ModuleError(f"Failed to load manifest for '{self.module_name}': {e}")

        if not "id" in module_data:
            log("warn", f"Missing id of '{self.module_name}', using package name as id instead.")
            module_data["id"] = self.module_name

        if not "name" in module_data:
            log("warn", f"Module name of '{self.module_name}' not defined, leaving empty.")
        else:
            self.module_name = module_data["name"]

        if not "description" in module_data:
            log("warn", f"Missing description of '{module_data['name']}'.")

        if not "author" in module_data:
            log("warn", f"Author of '{module_data['name']}' not defined.")

        if not "requires" in module_data:
            log("warn", f"Requirements of '{module_data['name']}' not defined.")

        else:
            requirements = module_data["requires"]
            if not "fpp" in requirements:
                log("warn", f"Required Flask++ version of '{module_data['name']}' not defined.")
            else:
                fulfilled = check_required_version(requirements["fpp"])
                if not fulfilled:
                    raise ModuleError(
                        f"Module '{module_data['name']}' requires Flask++ version {requirements['fpp']}."
                    )
            if "modules" in requirements:
                from flaskpp.modules import installed_modules
                modules = installed_modules(Path(self.root_path).parent)
                requirement = requirements["modules"]

                if isinstance(requirement, str):
                    requirement = [requirement]

                if isinstance(requirement, list):
                    new = {}
                    for r in requirement:
                        if not isinstance(r, str):
                            raise ManifestError(f"Invalid module requirement '{r}' for '{module_data['name']}'.")
                        r = r.split("@")
                        if len(r) == 2:
                            m, v = r
                        else:
                            m = r[0]
                            v = "*"
                        new[m] = v
                    requirement = new

                if not isinstance(requirement, dict):
                    raise ManifestError(f"Invalid modules requirement type '{requirement}' for '{module_data['name']}'.")

                required_modules = [m for m in requirement]
                fulfilled_modules = []

                for module in modules:
                    m, v = module
                    if not m in required_modules:
                        continue
                    if check_required_version(requirement[m], "module", v):
                        fulfilled_modules.append(m)

                if len(required_modules) != len(fulfilled_modules):
                    missing = [m for m in required_modules if m not in fulfilled_modules]
                    raise ModuleError(
                        f"Missing or mismatching module requirements for '{module_data['name']}': {missing}"
                    )

        return module_data

    def init_routes(self):
        try:
            routes = import_module(f"{self.import_name}.routes")
            init = getattr(routes, "init_routes", None)
            if not init:
                raise ImportError("Missing init function in routes.")
            init(self)
        except (ModuleNotFoundError, ImportError, TypeError) as e:
            log("warn", f"Failed to register routes for {self.module_name}: {e}")

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

    def render_template(self, template: str, **context) -> str:
        render_name = template if self.home else f"{self.name}/{template}"

        return render_template(render_name, **context)

    def on_enable(self, fn: Callable) -> Callable:
        if not takes_arg(fn, "app") or required_arg_count(fn) != 1:
            raise EventHookException(f"{self.import_name}.on_enable must take exactly one non optional argument: 'app'.")
        self._on_enable = fn
        return fn

    @property
    def version(self) -> ModuleVersion:
        return valid_version(self.info.get("version", ""))


def version_check(v: str) -> tuple[bool, str]:
    version_str = v.lower().strip()
    if not version_str:
        return False, "Module version not defined."

    first_char_invalid = False
    try:
        if version_str.startswith("v"):
            version_str = version_str[1:]
        int(version_str[0])
    except ValueError:
        first_char_invalid = True

    if  first_char_invalid \
            or (" " in version_str and not (version_str.endswith("alpha") or version_str.endswith("beta"))):
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

    return module_data


def valid_version(version: str) -> ModuleVersion:
    check = version_check(version)
    if not check[0]:
        raise ManifestError(check[1])

    return ModuleVersion(*map(int, check[1].split(".")))
