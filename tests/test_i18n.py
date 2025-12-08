from flask import Flask
from babel.support import Translations
from unittest.mock import patch, MagicMock

from flaskpp.app.i18n import (
    DBMergedTranslations,
    DBDomain,
    init_i18n
)


class DummyTranslations(Translations):
    def gettext(self, message):
        return f"mo:{message}"

    def ngettext(self, singular, plural, n):
        return f"mo:{singular if n == 1 else plural}"


@patch("flaskpp.app.i18n.I18nMessage")
def test_dbmerged_gettext_db_hit(mock_model):
    row = MagicMock()
    row.text = "db-value"
    mock_model.query.filter_by.return_value.first.return_value = row

    wrapped = DummyTranslations()
    dbt = DBMergedTranslations(wrapped, "messages", "en")

    assert dbt.gettext("hello") == "db-value"


@patch("flaskpp.app.i18n.I18nMessage")
def test_dbmerged_gettext_no_db_fallback(mock_model):
    mock_model.query.filter_by.return_value.first.return_value = None

    wrapped = DummyTranslations()
    dbt = DBMergedTranslations(wrapped, "messages", "en")

    assert dbt.gettext("hello") == "mo:hello"


@patch("flaskpp.app.i18n.I18nMessage")
def test_dbmerged_ngettext_db_hit(mock_model):
    row = MagicMock()
    row.text = "db-plural"
    mock_model.query.filter_by.return_value.first.return_value = row

    wrapped = DummyTranslations()
    dbt = DBMergedTranslations(wrapped, "messages", "en")

    assert dbt.ngettext("one", "many", 2) == "db-plural"


@patch("flaskpp.app.i18n.I18nMessage")
def test_dbmerged_ngettext_fallback(mock_model):
    mock_model.query.filter_by.return_value.first.return_value = None

    wrapped = DummyTranslations()
    dbt = DBMergedTranslations(wrapped, "messages", "en")

    assert dbt.ngettext("one", "many", 2) == "mo:many"


@patch("flaskpp.app.i18n.get_locale", return_value="en")
@patch("flaskpp.app.i18n.Translations.load")
def test_dbdomain_returns_dbmerged(mock_load, mock_locale):
    mock_load.return_value = DummyTranslations()

    domain = DBDomain(domain="messages")

    app = Flask(__name__)
    with app.app_context():
        translations = domain.get_translations()

    assert isinstance(translations, DBMergedTranslations)


def test_init_i18n_registers_jinja_globals():
    app = Flask(__name__)
    init_i18n(app)

    assert "_" in app.jinja_env.globals
    assert "ngettext" in app.jinja_env.globals
