from flask_babelplus import Domain
from babel.support import Translations
from flask import Flask, current_app

from flaskpp.app.extensions import socket
from flaskpp.app.data.babel import I18nMessage


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
    def __init__(self, dirname=None, domain="messages"):
        super().__init__(dirname, domain)
        self.registered_domains = []

    def get_translations(self, domain: str = None):
        from flaskpp.app.utils.translating import get_locale
        locale = get_locale()
        cache = self.get_translations_cache()

        if not domain:
            domain = self.domain

        key = f"{locale}@{domain}"
        translations = cache.get(key)
        if translations is None:
            wrapped = Translations.load(
                dirname=current_app.config.get("BABEL_TRANSLATION_DIRECTORIES", "translations"),
                locales=locale,
                domain=domain
            )
            translations = DBMergedTranslations(wrapped, domain=domain, locale=locale)
            self.cache[key] = translations

        return translations


def init_i18n(app: Flask):
    from flaskpp.app.utils.translating import t, tn
    app.jinja_env.globals.update(
        _=t,
        ngettext=tn
    )

    @socket.on_default("_")
    def socket_t(key: str) -> str:
        return t(key)

    @socket.on_default("_n")
    def socket_tn(data: dict) -> str:
        return tn(
            data.get("s", ""),
            data.get("p", ""),
            data.get("n", 0)
        )
