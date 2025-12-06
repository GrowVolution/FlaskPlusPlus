from typing import Callable

nav_links = {}


def autonav_route(blueprint, rule: str, label: str, **route_kwargs) -> Callable:
    prefix = blueprint.url_prefix or ""
    full_path = f"{prefix}{rule}"
    nav_links[label] = full_path

    def decorator(func):
        blueprint.add_url_rule(rule, view_func=func, **route_kwargs)
        return func

    return decorator
