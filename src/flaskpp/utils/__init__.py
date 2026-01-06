from functools import wraps
from typing import Callable, Any, TYPE_CHECKING
import os, string, random, socket, inspect, re

from flaskpp.utils.debugger import log

if TYPE_CHECKING:
    from flaskpp import FppVersion, ModuleVersion


def random_code(length: int = 6) -> str:
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))


def prompt_yes_no(question: str) -> bool:
    answer = input(question).lower().strip()
    if answer in ('y', 'yes', '1'):
        return True
    return False


def enabled(key: str) -> bool:
    return os.getenv(key, "false").lower() in ["true", "1", "yes"]


def is_port_free(port, host="127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


def safe_string(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", text)


def sanitize_text(value: str) -> str:
    return value.encode("utf-8", "ignore").decode("utf-8")


def takes_arg(fn: Callable, arg: str) -> bool:
    sig = inspect.signature(fn)
    return arg in sig.parameters


def required_arg_count(fn: Callable) -> int:
    sig = inspect.signature(fn)

    return sum(
        1
        for p in sig.parameters.values()
        if p.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        )
        and p.default is inspect._empty
    )


def decorate(decorator: Callable, handler: Callable) -> Callable:
    if handler is None:
        return decorator
    return decorator(handler)


async def async_result(result: Any) -> Any:
    if inspect.isawaitable(result):
        return await result
    return result


def check_required_version(requirement: str, version_type: str = "fpp", module_version: "ModuleVersion | str" = None) -> bool:
    version_type = version_type.lower()
    if version_type not in ["fpp", "module"]:
        raise ValueError("Invalid version type.")

    if version_type == "module" and module_version is None:
        raise RuntimeError("Cannot check with unknown module version.")

    from flaskpp import FppVersion, ModuleVersion, version
    ver_cls = FppVersion if version_type == "fpp" else ModuleVersion

    if requirement != "*":
        for candidate in (">=", "<=", "==", ">", "<"):
            if requirement.startswith(candidate):
                op = candidate
                ver = requirement[len(candidate):].strip()
                break
        else:
            raise ValueError(f"Invalid version operator in requirement '{requirement}'")
    else:
        return True

    if version_type == "module":
        current = module_version if isinstance(module_version, ver_cls) \
            else ver_cls(*map(int, module_version.split(".")))
    else:
        current = version()

    try:
        target = ver_cls(*map(int, ver.split(".")))
    except ValueError:
        raise ValueError("Invalid requirement string.")

    return {
        ">":  current > target,
        ">=": current >= target,
        "<":  current < target,
        "<=": current <= target,
        "==": current == target,
    }.get(op, False)


def require_extensions(*extensions):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for ext in extensions:
                if not isinstance(ext, str):
                    log("warn", f"Invalid extension '{ext}'.")
                    continue

                if not enabled(f"EXT_{ext.upper()}"):
                    raise RuntimeError(f"Extension '{ext}' is not enabled.")
            return func(*args, **kwargs)

        return wrapper
    return decorator
