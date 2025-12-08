from flask import Blueprint
from pathlib import Path
import json

from flaskpp import FlaskPP
from flaskpp.modules import require_extensions, ManifestError
from .data import init_models

NAME = __name__
bp = Blueprint(NAME, NAME, template_folder="templates", static_folder="static")

manifest = Path(__file__).parent / "manifest.json"
module_data = {}


@bp.context_processor
def context_processor():
    return dict(
        NAME=NAME
    )


@require_extensions("sqlalchemy")
def register_module(app: FlaskPP, home: bool):
    if home:
        bp.static_url_path = f"/{NAME}/static"
    else:
        bp.url_prefix = f"/{NAME}"

    from .routes import init_routes
    init_routes(bp)

    app.register_blueprint(bp)
    init_models()


def version() -> str:
    version_str = module_data.get("version", "").lower().strip()
    if not version_str:
        raise ManifestError("Module version not defined.")

    if " " in version_str and not (version_str.endswith("alpha") or version_str.endswith("beta")):
        raise ManifestError("Invalid version string format.")

    if version_str.startswith("v"):
        version_str = version_str[1:]

    try:
        v_numbers = version_str.split(" ")[0].split(".")
        if len(v_numbers) > 3:
            raise ManifestError("Too many version numbers.")

        for v_number in v_numbers:
            int(v_number)
    except ValueError:
        raise ManifestError("Invalid version numbers.")

    return version_str


def __init__():
    global module_data

    if not manifest.exists():
        raise FileNotFoundError(f"Manifest file for {NAME} not found.")

    try:
        module_data = json.loads(manifest.read_text())
    except json.decoder.JSONDecodeError:
        raise ManifestError(f"Invalid format for manifest of {NAME}.")

    if not "name" in module_data:
        module_data["name"] = NAME

    if not "description" in module_data:
        RuntimeWarning(f"Missing description of {module_data['name']}.")

    if not "version" in module_data:
        raise ManifestError("Module version not defined.")

    if not "author" in module_data:
        RuntimeWarning(f"Author of {module_data['name']} not defined.")


def __repr__():
    return f"<{module_data['name']} {version()}> {module_data.get('description', '')}"
