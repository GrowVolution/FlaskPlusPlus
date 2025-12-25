from pathlib import Path
import os, string, random, socket


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


def sanitize_text(value: str) -> str:
    return value.encode("utf-8", "ignore").decode("utf-8")
