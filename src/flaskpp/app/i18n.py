from flask_babelplus import Domain
from babel.support import Translations
from flask import Flask, current_app

from flaskpp.app.data.babel import I18nMessage
from flaskpp.app.utils.translating import t, tn, get_locale


class DBMergedTranslations(Translations):
    def __init__(self, wrapped: Translations, domain: str, locale: str):
        super().__init__()
        self._wrapped = wrapped
        self._domain = domain
        self._locale = locale

    def _db_get(self, msgid):
        row = (
            I18nMessage.query
            .filter_by(domain=self._domain, locale=self._locale, key=msgid)
            .first()
        )
        return row.text if row else None

    def gettext(self, message):
        db_val = self._db_get(message)
        if db_val:
            return db_val
        mo_val = self._wrapped.gettext(message)
        return mo_val

    def ngettext(self, singular, plural, n):
        key = plural if n != 1 else singular
        db_val = self._db_get(key)
        if db_val:
            return db_val
        mo_val = self._wrapped.ngettext(singular, plural, n)
        return mo_val


class DBDomain(Domain):
    def get_translations(self):
        locale = get_locale()

        wrapped = Translations.load(
            dirname=current_app.config.get("BABEL_TRANSLATION_DIRECTORIES", "translations"),
            locales=locale,
            domain=self.domain or "messages"
        )

        return DBMergedTranslations(wrapped, domain=self.domain, locale=locale)


def init_i18n(app: Flask):
    app.jinja_env.globals.update(
        _=t,
        ngettext=tn
    )
