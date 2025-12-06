
CONFIG_MAP = {}


def register_config(name: str):
    def decorator(cls):
        CONFIG_MAP[name] = cls
        return cls
    return decorator
