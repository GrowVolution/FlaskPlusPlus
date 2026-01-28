from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Flask, Blueprint


class Link:
    def __init__(self, label: str, href: str, additional_classes: str = ""):
        self.label = label
        self.href = href
        self.classes = additional_classes


class Dropdown:
    def __init__(self, label: str, additional_classes: str = ""):
        self.label = label
        self.links = []
        self.classes = additional_classes

_nav_links: dict[int, list[Link]] = {}
_nav_dropdowns: dict[int, list[Dropdown]] = {}


class DropdownBuilder:
    def __init__(
        self, dropdown_label: str, dropdown_priority: int = 1,
        additional_dropdown_classes: str = ""
    ):
        _check(dropdown_priority)

        self.priority = dropdown_priority
        self.dropdown = Dropdown(dropdown_label, additional_dropdown_classes)
        self.dropdown_links = {}

        self.saved = False

    def dropdown_route(
        self, target: "Flask | Blueprint", rule: str,
        label: str, priority: int = 1,
        additional_classes: str = "",
        **route_kwargs
    ):
        if self.saved:
            raise RuntimeError("Dropdown already saved.")
        _check(priority)

        if not priority in self.dropdown_links:
            self.dropdown_links[priority] = []
        self.dropdown_links[priority].append(Link(
            label, _path(target, rule),
            additional_classes
        ))

        def decorator(func):
            target.add_url_rule(rule, view_func=func, **route_kwargs)
            return func

        return decorator

    def save(self):
        if self.saved:
            raise RuntimeError("Dropdown already saved.")

        from flaskpp.utils import build_sorted_tuple
        for i, links in enumerate(
            build_sorted_tuple(self.dropdown_links)
        ):
            self.dropdown.links.extend(links)
            if i < len(self.dropdown_links) - 1:
                self.dropdown.links.append(None)

        if not self.priority in _nav_dropdowns:
            _nav_dropdowns[self.priority] = []
        _nav_dropdowns[self.priority].append(self.dropdown)

        self.saved = True


def _check(priority: int):
    from flaskpp.utils import check_priority
    check_priority(priority)


def _path(t: "Flask | Blueprint", rule: str) -> str:
    prefix = t.url_prefix or ""
    return f"{prefix}{rule}"


def autonav_route(
    target: "Flask | Blueprint", rule: str,
    label: str, priority: int = 1,
    additional_classes: str = "",
    **route_kwargs
) -> Callable:
    _check(priority)

    if not priority in _nav_links:
        _nav_links[priority] = []
    _nav_links[priority].append(Link(
        label, _path(target, rule),
        additional_classes
    ))

    def decorator(func):
        target.add_url_rule(rule, view_func=func, **route_kwargs)
        return func

    return decorator


def build_nav() -> dict:
    from flaskpp.utils import build_sorted_tuple

    nav = {
        "links": [],
        "dropdowns": []
    }

    for links in build_sorted_tuple(_nav_links):
        nav["links"].extend(links)

    for dropdowns in build_sorted_tuple(_nav_dropdowns):
        nav["dropdowns"].extend(dropdowns)

    return nav
