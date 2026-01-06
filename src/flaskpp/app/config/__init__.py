from typing import Callable

CONFIG_MAP = {}


def register_config(name: str) -> Callable:
    def decorator(cls):
        CONFIG_MAP[name] = cls
        return cls
    return decorator
