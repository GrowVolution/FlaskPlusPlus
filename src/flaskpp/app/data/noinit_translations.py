from flaskpp.babel import valid_state
from flaskpp.utils import enabled
from flaskpp.app.utils.i18n import update_translations
from flaskpp.exceptions import I18nError


translations: dict[str, dict[str, str]] = {}

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
    "FORBIDDEN_TITLE",
    "FORBIDDEN_MSG",

]

translations["en"] = {
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
    _msg_keys[12]: "Access Denied",
    _msg_keys[13]: "You are not authorized to access this page.",

}

translations["de"] = {
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
    _msg_keys[12]: "Zugriff Verweigert",
    _msg_keys[13]: "Du bist nicht berechtigt auf diese Seite zuzugreifen."

}


def setup_db(domain: str = "flaskpp"):
    if not (enabled("EXT_BABEL") and enabled("EXT_SQLALCHEMY")):
        raise I18nError("To setup Flask++ base translations, you must enable EXT_BABEL and EXT_SQLALCHEMY.")

    state = valid_state()
    state.fpp_fallback_domain = domain
    update_translations("Flask++", __name__, domain)
