from flask import render_template as _render_template

from . import NAME


def render_template(template: str, **context) -> str:
    return _render_template(f"{NAME}/{template}", **context)
