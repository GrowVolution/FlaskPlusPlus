from pathlib import Path
from importlib import import_module
from typing import Callable, TYPE_CHECKING

from flaskpp.utils import check_priority, build_sorted_tuple
from flaskpp.app.config.default import DefaultConfig

if TYPE_CHECKING:
    from flaskpp import FlaskPP

_config_map: dict[int, list[type]] = {}


def init_configs(app: "FlaskPP"):
    modules = Path(app.root_path) / "modules"
    for module in modules.iterdir():
        if not module.is_dir():
            continue

        config = module / "config.py"
        if config.exists():
            import_module(f"modules.{module.name}.config")


def register_config(priority: int = 1) -> Callable:
    check_priority(priority)

    def decorator(cls):
        if not priority in _config_map:
            _config_map[priority] = []
        _config_map[priority].append(cls)
        return cls
    return decorator


def build_config() -> type:
    return type(
        "Config",
        build_sorted_tuple(_config_map, (DefaultConfig, )),
        {}
    )
