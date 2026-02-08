
extensions = [
    "sqlalchemy",
    "socket",
    "babel",
    "fst",
    "authlib",
    "mailing",
    "cache",
    "api",
    "jwt_extended"
]


module_init = """from flaskpp import Module
{extend_import}

module = Module(
    __file__,
    __name__,{extend}{requires}{is_base}
)"""


module_handling = """from pathlib import Path
from importlib import import_module

from flaskpp import Module

_package = Path(__file__).parent


def init_handling(mod: Module):
    for file in _package.rglob("*.py"):
        if file.stem == "__init__" or file.stem.startswith("noinit"):
            continue

        rel = file.relative_to(_package).with_suffix("")
        handler_name = ".".join(rel.parts)

        handler = import_module(f"{mod.import_name}.handling.{handler_name}")
        handle_request = getattr(handler, "handle_request", None)
        if not handle_request:
            continue

        mod.handler(handler_name)(handle_request)"""


handling_example = """from flask import flash, redirect

from flaskpp import Module
from flaskpp.utils import enabled


def handle_request(mod: Module, *args):
    if not enabled("FRONTEND_ENGINE"):
        flash("Vite is not enabled for this app.", "warning")
        return redirect("/")
    return mod.render_template("vite_index.html")"""


module_routes = """from flaskpp import Module
from flaskpp.app.utils.auto_nav import autonav_route


def init_routes(mod: Module):
    @mod.route("/")
    def index():
        return mod.render_template("index.html")
        
    autonav_route(mod, "/vite-index", mod.t("Vite Test"))(
        mod.handle_request("vite_index")
    )"""


module_config = """# from security import token_hex
{config_import}
from . import module

{register}
class {name}Config(module.base_config):
    # TODO: Write your modules required config data here
    pass
    
    
def module_config():
    # return {{
        # TODO: Write required config data (will be prompted by the setup if module is set to 1)
        
        # "protected_MY_SECRET": token_hex(32),
        # -> protected keys won't be prompted to the user
        
        # "default_FEATURE_KEY": "Hello World!",
        # -> default keys will be prompted with their default value shown (and written with if input left empty)
        
        # "ADDITIONAL_DATA": "",
        # -> simple config prompt without default value
    # }}
    pass{config_export}"""


module_index = """{% extends "base_example.html" %}
{# The base template is natively provided by Flask++. #}

{% block title %}{{ _('My Module') }}{% endblock %}
{% block head %}{{ tailwind }}{% endblock %}

{% block content %}
    <div class="flex flex-col min-h-[100dvh] items-center justify-center px-6 py-8">
        <h2 class="text-2xl font-semibold">{{ _('Welcome!') }}</h2>
        <p class="mt-2">{{ _('This is my wonderful new module.') }}</p>
    </div>
{% endblock %}"""


module_vite_index = """{% extends "base_example.html" %}

{% block title %}{{ _('Home') }}{% endblock %}
{% block head %}{{ vite('main.js') }}{% endblock %}"""


module_data_init = """from pathlib import Path
from importlib import import_module

from flaskpp import Module

_package = Path(__file__).parent


def init_models(mod: Module):
    for file in _package.rglob("*.py"):
        if file.stem == "__init__" or file.stem.startswith("noinit"):
            continue
        rel = file.relative_to(_package).with_suffix("")
        import_module(f"{mod.import_name}.data.{".".join(rel.parts)}")"""


tailwind_raw = """@import "tailwindcss" source("../../");

@source not "../../vite";

@theme {
    /* ... */
}"""
