
default_handlers = {}


def default_event(name: str):
    def decorator(func):
        default_handlers[name] = func
        return func
    return decorator


def no_handler(_):
    raise NotImplementedError("Socket event handler not found.")
