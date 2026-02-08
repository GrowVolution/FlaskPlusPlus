from flask import render_template, current_app
from jinja2 import TemplateNotFound
from flask_mailman import EmailMultiAlternatives
from threading import Thread
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flaskpp import Module


def _safe_render(template: str, module: "Module", context: dict) -> str:
    try:
        return render_mail_template(template, module, **context)
    except TemplateNotFound:
        return ""


def render_mail_template(template: str, module: "Module" = None, **context) -> str:
    if module is None:
        return render_template(f"app/email/{template}", **context)
    return module.render_template(f"email/{template}", **context)


def send_email(subject: str, recipient: str, email_template: str,
               sender_name: str = None, module: "Module" = None, **context):
    body = _safe_render(f"{email_template}.txt", module, context)
    html = _safe_render(f"{email_template}.html", module, context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=body,
        to=[recipient]
    )
    msg.attach_alternative(html, "text/html")

    if sender_name:
        user = current_app.config.get("MAIL_USERNAME", "noreply@example.com")
        msg.from_email = f"{sender_name} <{user}>"

    Thread(target=msg.send).start()
