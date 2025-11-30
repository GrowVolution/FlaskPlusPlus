from flask_babelplus import Domain
from babel.support import Translations
from flask import Flask, current_app

from .data.babel import I18nMessage
from .utils.translating import t, tn, get_locale
from utils.debugger import debug_msg


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
            debug_msg(f"[i18n] DB hit: {message!r} → {db_val!r}")
            return db_val
        mo_val = self._wrapped.gettext(message)
        debug_msg(f"[i18n] MO/fallback: {message!r} → {mo_val!r}")
        return mo_val

    def ngettext(self, singular, plural, n):
        key = plural if n != 1 else singular
        db_val = self._db_get(key)
        if db_val:
            debug_msg(f"[i18n] DB plural hit: {key!r} → {db_val!r}")
            return db_val
        mo_val = self._wrapped.ngettext(singular, plural, n)
        debug_msg(f"[i18n] MO plural: {singular!r}/{plural!r} → {mo_val!r}")
        return mo_val


class DBDomain(Domain):
    def get_translations(self):
        locale = get_locale()

        wrapped = Translations.load(
            dirname=current_app.config.get("BABEL_TRANSLATION_DIRECTORIES", "translations"),
            locales=locale,
            domain=self.domain or "messages"
        )

        debug_msg(f"domain={self.domain}, locale={locale}, has_wrapped={wrapped is not None}")
        return DBMergedTranslations(wrapped, domain=self.domain, locale=locale)


def init_i18n(app: Flask):
    app.jinja_env.globals.update(
        _=t,
        ngettext=tn
    )
