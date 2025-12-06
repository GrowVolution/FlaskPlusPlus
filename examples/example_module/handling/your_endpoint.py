from flask import flash, redirect, request, url_for, render_template

from .. import NAME
from ..forms import ContactForm
from ..data.your_dataset import YourModel
from app.utils.translating import t
from app.data import add_model


def handle_request():
    form = ContactForm()

    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        message = form.message.data

        db_entry = YourModel(name, email, message)
        add_model(db_entry)

        flash(t("Thanks! Your message has been received."), "success")
        return redirect(url_for(f"{NAME}.endpoint"))

    if request.method == "POST" and not form.validate():
        flash(t("Please check your inputs."), "danger")

    return render_template("your_form.html", form=form)
