from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length


class ContactForm(FlaskForm):
    from app.utils.translating import t
    name = StringField(t("Name"), validators=[DataRequired(), Length(max=80)])
    email = StringField(t("E-Mail"), validators=[DataRequired(), Email(), Length(max=120)])
    message = TextAreaField(t("Message"), validators=[DataRequired(), Length(max=2000)])
    agree = BooleanField(t("I accept the privacy guideline"), validators=[DataRequired()])
    submit = SubmitField(t("Send"))
