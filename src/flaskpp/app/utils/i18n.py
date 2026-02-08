from pathlib import Path
from importlib import import_module
import json

from flaskpp.app.data.babel import add_entry, get_entries
from flaskpp.app.data import commit, delete_model
from flaskpp.babel import valid_state
from flaskpp.utils import enabled
from flaskpp.utils.logging import log
from flaskpp.exceptions import I18nError


def _add_entries(translations: dict, key: str, domain: str):
    for locale, t in translations.items():
        if key not in t:
            continue
        add_entry(locale, key, t[key], domain, False)


def get_locale_data(locale: str) -> tuple[str, str]:
    if len(locale) != 2 and len(locale) != 5 or len(locale) == 5 and "_" not in locale:
        raise I18nError(f"Invalid locale code: {locale}")

    if "_" in locale:
        locale = locale.split("_")[0]

    try:
        locale_data = json.loads(
            (Path(__file__).parent.parent / "data" / "locales.json").read_text(encoding="utf-8")
        )
    except json.JSONDecodeError:
        raise I18nError("Failed to parse locales.json")

    flags = locale_data.get("flags", {})
    names = locale_data.get("names", {})
    return flags.get(locale, "🇬🇧"), names.get(locale, "English")


def update_translations(executor: str, translations_import_name: str, domain: str = None):
    default_domain = valid_state().domain.domain
    if not domain:
        domain = default_domain
    entries = get_entries(domain=domain)

    translations_module = import_module(translations_import_name)
    translations_dict = getattr(translations_module, "translations", {})

    fb_translations = {}
    for t in translations_dict.values():
        fb_translations = t
        break
    msg_keys = [k for k in fb_translations]

    if entries and enabled("I18N_AUTOUPDATE"):
        log(f"[{executor}] Updating translations...")

        keys = [e.key for e in entries]
        for key in msg_keys:
            if key not in keys:
                _add_entries(translations_dict, key, domain)


        for entry in entries:
            key = entry.key
            translations = translations_dict.get(entry.locale, translations_dict.get("en"))
            if not translations:
                translations = fb_translations

            try:
                if translations[key] != entry.text:
                    entry.text = translations[key]
            except KeyError:
                if domain == default_domain:
                    continue
                delete_model(entry, False)
    else:
        log(f"[{executor}] Setting up translations...")

        for key in msg_keys:
            _add_entries(translations_dict, key, domain)

    commit()