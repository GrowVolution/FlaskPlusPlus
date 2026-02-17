import traceback, sys, logging

_execution = False
_initialized = False

DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL


def _get_logger(level: int = INFO) -> logging.Logger:
    global _initialized
    if _initialized:
        return logging.getLogger("Flask++")

    logger = logging.getLogger("Flask++")
    logger.setLevel(level)
    logger.propagate = False

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.NOTSET)

    formatter = logging.Formatter(
        "[%(name)s]\t[%(asctime)s] [%(levelname)s]\t%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S %z"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    _initialized = True
    return logger


def log(message: str, category: int = INFO):
    if not _execution:
        return

    if not _logger:
        raise RuntimeError("You must call start_session before you start logging.")

    _get_logger().log(category, message)
    print(category, message)


def exception(exc: Exception, message: str = None):
    msg = f"{message.strip()}\n" if message else ""
    tb_str = "".join(traceback.format_exception(*sys.exc_info()))
    error(f"{msg}{type(exc).__name__}: {exc}\n{tb_str.strip()}")


def start_session(level: str = "info"):
    global _execution
    from flaskpp.utils import enabled
    _execution = enabled("IN_EXECUTION")
    if not _execution:
        return

    global _logger
    level = level.upper()
    _logger = _get_logger(getattr(logging, level, INFO))

    log("Starting Flask++ application.")


def debug(msg): log(msg, DEBUG)
def warn(msg): log(msg, WARNING)
def error(msg): log(msg, ERROR)
def critical(msg): log(msg, CRITICAL)
