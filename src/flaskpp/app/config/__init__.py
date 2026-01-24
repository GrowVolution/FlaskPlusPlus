from pathlib import Path
from importlib import import_module
from typing import Callable, TYPE_CHECKING

from flaskpp.app.config.default import DefaultConfig
from flaskpp.utils import check_priority, build_sorted_tuple

if TYPE_CHECKING:
    from flaskpp import FlaskPP

_config_map: dict[int, list[type]] = {}


class ConfigMeta(type): pass


def init_configs(app: "FlaskPP"):
    modules = Path(app.root_path) / "modules"

    if not modules.exists() or not modules.is_dir():
        return

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

        if not isinstance(type(cls), ConfigMeta):
            cls = ConfigMeta(cls.__name__, cls.__bases__, dict(cls.__dict__))

        _config_map[priority].append(cls)
        return cls

    return decorator


def build_config() -> ConfigMeta:
    cls = DefaultConfig
    default_conf = ConfigMeta(cls.__name__, cls.__bases__, dict(cls.__dict__))

    bases = tuple()
    for configs in build_sorted_tuple(_config_map):
        bases += tuple(configs)

    return ConfigMeta(
        "Config",
        bases + (default_conf, ),
        {}
    )
