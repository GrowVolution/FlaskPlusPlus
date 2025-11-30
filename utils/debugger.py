from datetime import datetime
import traceback, sys

_debug = False


def get_time() -> str:
    offset = datetime.now().astimezone().utcoffset()
    hours = int(offset.total_seconds() // 3600)
    minutes = int((offset.total_seconds() % 3600) // 60)

    sign = '+' if offset.total_seconds() >= 0 else '-'
    offset_str = f"{sign}{abs(hours):02d}{abs(minutes):02d}"

    return f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {offset_str}"


def log(category: str, message: str):
    log_str = f"[FLASK]\t[{get_time()}] [{category.upper()}] {message}"
    print(log_str)


def exception(error: Exception, message: str = None):
    if _debug:
        tb_str = "".join(traceback.format_exception(*sys.exc_info()))
    else:
        tb_str = "".join(traceback.format_exc(limit=3))
    msg = f"{message.strip()}\n" if message else ""
    log("exception", f"{msg}{type(error).__name__}: {error}\n{tb_str.strip()}")


def debug_msg(message: str):
    if _debug:
        log("debug", message)


def start_session(debug: bool):
    global _debug
    _debug = debug
    log("info", "Flask plug & play module server running.")
    log("info", f"Loglevel {'debug' if debug else 'info'}.")
