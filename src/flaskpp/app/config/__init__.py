from pathlib import Path
from importlib import import_module
from typing import Callable, TYPE_CHECKING

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
    if priority not in range(11):
        raise ValueError("Priority must be between 1 and 10.")

    def decorator(cls):
        if not priority in _config_map:
            _config_map[priority] = []
        _config_map[priority].append(cls)
        return cls
    return decorator


def build_config() -> type:
    configs = dict(sorted(_config_map.items(), reverse=True)).values()
    bases = tuple(configs) + (DefaultConfig, )
    return type("Config", bases, {})
