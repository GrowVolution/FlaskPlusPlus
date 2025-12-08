from flaskpp.app.data import add_model, delete_model, commit
from flaskpp.app.extensions import db


class I18nMessage(db.Model):
    __tablename__ = "i18n_messages"
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(64), nullable=False, default="messages")
    locale = db.Column(db.String(16), nullable=False)
    key = db.Column(db.String(255), nullable=False)
    text = db.Column(db.Text, nullable=False)

    __table_args__ = (db.UniqueConstraint("domain", "locale", "key"),)

    def __init__(self, domain, locale, key, text):
        self.domain = domain
        self.locale = locale
        self.key = key
        self.text = text


def add_entry(locale: str, key: str, text: str, domain: str = "messages"):
    entry = I18nMessage(domain, locale, key, text)
    add_model(entry)


def get_entry(key: str, domain: str = "messages"):
    return I18nMessage.query.filter_by(key=key, domain=domain).first()


def get_entries(**filters):
    return I18nMessage.query.filter_by(**filters).all()


def remove_entry(key: str, locale: str, domain: str = "messages"):
    entry = I18nMessage.query.filter_by(key=key, locale=locale, domain=domain).first()
    if entry:
        delete_model(entry)


def remove_entries(key: str):
    entries = I18nMessage.query.filter_by(key=key).all()
    for entry in entries:
        delete_model(entry, False)
    commit()
