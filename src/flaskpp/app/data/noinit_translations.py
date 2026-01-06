import json

from flaskpp.app.data import commit, _package
from flaskpp.app.data.babel import add_entry, get_entries
from flaskpp.babel import valid_state
from flaskpp.utils import enabled
from flaskpp.utils.debugger import log
from flaskpp.exceptions import I18nError

_msg_keys = [
    "NAV_BRAND",
    "NOT_FOUND_TITLE",
    "NOT_FOUND_MSG",
    "BACK_HOME",
    "ERROR",
    "ERROR_TITLE",
    "ERROR_MSG",
    "CONFIRM",
    "YES",
    "NO",
    "HINT",
    "UNDERSTOOD",

]

_translations_en = {
    _msg_keys[0]: "My Flask++ App",
    _msg_keys[1]: "Not Found",
    _msg_keys[2]: "We are sorry, but the requested page doesn't exist.",
    _msg_keys[3]: "Back Home",
    _msg_keys[4]: "Error",
    _msg_keys[5]: "An error occurred",
    _msg_keys[6]: "Something went wrong, please try again later.",
    _msg_keys[7]: "Confirm",
    _msg_keys[8]: "Yes",
    _msg_keys[9]: "No",
    _msg_keys[10]: "Hint",
    _msg_keys[11]: "Understood",

}

_translations_de = {
    _msg_keys[0]: "Meine Flask++ App",
    _msg_keys[1]: "Nicht Gefunden",
    _msg_keys[2]: "Wir konnten die angefragte Seite leider nicht finden.",
    _msg_keys[3]: "Zurück zur Startseite",
    _msg_keys[4]: "Fehler",
    _msg_keys[5]: "Ein Fehler ist aufgetreten",
    _msg_keys[6]: "Leider ist etwas schief gelaufen, bitte versuche es später erneut.",
    _msg_keys[7]: "Bestätigen",
    _msg_keys[8]: "Ja",
    _msg_keys[9]: "Nein",
    _msg_keys[10]: "Hinweis",
    _msg_keys[11]: "Verstanden",

}


def _add_entries(key: str, domain: str):
    add_entry("en", key, _translations_en[key], domain, False)
    add_entry("de", key, _translations_de[key], domain, False)


def setup_db(domain: str = "flaskpp"):
    if not (enabled("EXT_BABEL") and enabled("EXT_SQLALCHEMY")):
        raise I18nError("To setup Flask++ base translations, you must enable EXT_BABEL and EXT_SQLALCHEMY.")

    state = valid_state()
    state.fpp_fallback_domain = domain
    entries = get_entries(domain=domain, locale="en")

    if entries:
        log("info", f"Updating Flask++ base translations...")

        keys = [e.key for e in entries]
        for key in _msg_keys:
            if key not in keys:
                _add_entries(key, domain)

        for entry in entries:
            if _translations_en[entry.key] != entry.text:
                entry.text = _translations_en[entry.key]
    else:
        log("info", f"Setting up Flask++ translations...")

        for key in _msg_keys:
            _add_entries(key, domain)

    commit()


def get_locale_data(locale: str) -> tuple[str, str]:
    if len(locale) != 2 and len(locale) != 5 or len(locale) == 5 and "_" not in locale:
        raise I18nError(f"Invalid locale code: {locale}")

    if "_" in locale:
        locale = locale.split("_")[0]

    try:
        locale_data = json.loads((_package / "locales.json").read_text())
    except json.JSONDecodeError:
        raise I18nError("Failed to parse locales.json")

    flags = locale_data.get("flags", {})
    names = locale_data.get("names", {})
    return flags.get(locale, "🇬🇧"), names.get(locale, "English")
