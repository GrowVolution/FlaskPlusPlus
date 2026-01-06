from flask_babelplus import Babel, constants, utils
from typing import TYPE_CHECKING

from flaskpp.app.config.default import DefaultConfig
from flaskpp.exceptions import I18nError

if TYPE_CHECKING:
    from flask import Flask
    from werkzeug.datastructures import ImmutableDict
    from flaskpp import FlaskPP, Module


class FppBabel(Babel):

    default_config = DefaultConfig()

    def __init__(self, app: "FlaskPP | Flask" = None, **kwargs):
        super().__init__(app, **kwargs)
        self.date_formats = None

    def init_app(self, app: "FlaskPP | Flask", default_locale: str = None,
                 default_timezone: str = None, date_formats: "ImmutableDict[str, str | None]" = None,
                 configure_jinja: bool = True, default_domain: str = None):
        if default_domain is None:
            from flaskpp.i18n import DBDomain
            default_domain = DBDomain()

        if default_locale is None:
            app.config.setdefault('BABEL_DEFAULT_LOCALE', self.default_config.BABEL_DEFAULT_LOCALE)
        else:
            app.config.setdefault('BABEL_DEFAULT_LOCALE', default_locale)

        if default_timezone is None:
            app.config.setdefault('BABEL_DEFAULT_TIMEZONE', self.default_config.BABEL_DEFAULT_TIMEZONE)
        else:
            app.config.setdefault('BABEL_DEFAULT_TIMEZONE', default_timezone)

        app.config.setdefault('BABEL_CONFIGURE_JINJA', configure_jinja)
        app.config.setdefault('BABEL_DOMAIN', default_domain)

        app.extensions['babel'] = _FppBabelState(
            babel=self, app=app, domain=default_domain
        )

        self.date_formats = date_formats or constants.DEFAULT_DATE_FORMATS.copy()

        if configure_jinja:
            app.jinja_env.filters.update(
                datetimeformat=utils.format_datetime,
                dateformat=utils.format_date,
                timeformat=utils.format_time,
                timedeltaformat=utils.format_timedelta,

                numberformat=utils.format_number,
                decimalformat=utils.format_decimal,
                currencyformat=utils.format_currency,
                percentformat=utils.format_percent,
                scientificformat=utils.format_scientific,
            )
            app.jinja_env.add_extension('jinja2.ext.i18n')

            from flaskpp.app.utils.translating import t, tn
            app.jinja_env.install_gettext_callables(
                t, tn, newstyle=True
            )


class _FppBabelState(object):
    def __init__(self, babel: FppBabel, app: "FlaskPP | Flask", domain: str):
        self.babel = babel
        self.app = app
        self.domain = domain
        self.locale_cache = {}
        self.module_domains = {}
        self.fallback_domain = None
        self.fpp_fallback_domain = None

    def __repr__(self) -> str:
        return '<_FppBabelState({}, {}, {})>'.format(
            self.babel, self.app, self.domain
        )


def valid_state() -> _FppBabelState:
    state = utils.get_state(silent=True)
    if state is None:
        raise I18nError("Failed to load state: Running outside of application context.")
    if not isinstance(state, _FppBabelState):
        raise I18nError("Invalid state: Flask++ is using FppBabel, please avoid using any other Babel extension.")
    return state


def register_module(module: "Module", domain_name: str = None):
    state = valid_state()
    name = domain_name or module.name
    state.module_domains[name] = module
    module.context["DOMAIN"] = name


def set_fallback_domain(domain_name: str, protected: bool = False):
    state = valid_state()
    if state.fallback_domain is not None:
        _, prev_protected = state.fallback_domain
        if prev_protected:
            raise I18nError("Failed to set new fallback domain: Current one is protected.")
    state.fallback_domain = (domain_name, protected)
