from pathlib import Path
from importlib import import_module

_package = Path(__file__).parent


def init_models():
    from .. import NAME
    for file in _package.rglob("*.py"):
        if file.stem == "__init__":
            continue
        import_module(f"modules.{NAME}.data.{file.stem}")
