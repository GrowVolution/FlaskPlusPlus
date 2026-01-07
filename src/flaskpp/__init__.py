from pathlib import Path

from flaskpp.flaskpp import FlaskPP, FppVersion, version
from flaskpp.module import Module, ModuleVersion
from flaskpp.babel import FppBabel
from flaskpp.socket import FppSocket

_fpp_root = Path(__file__).parent.resolve()

__all__ = [
    "_fpp_root",

    "FlaskPP", "FppVersion", "version",
    "Module", "ModuleVersion",
    "FppBabel", "FppSocket"
]
