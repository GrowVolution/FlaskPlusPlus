import os, string, random


def random_code(length: int = 6) -> str:
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))


def prompt_yes_no(question: str) -> bool:
    answer = input(question).lower().strip()
    if answer in ('y', 'yes', '1'):
        return True
    return False


def enabled(key: str) -> bool:
    return os.getenv(key, "false").lower() in ["true", "1", "yes"]
