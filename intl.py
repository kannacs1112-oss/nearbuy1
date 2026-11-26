"""Internationalisation: languages, countries, currencies and time zones.

Standard library only, so these rules can be unit-tested without Flask installed.
Translations live in locales/<code>.json. The English source text is itself the key,
so a missing translation falls back to English rather than breaking the page.
"""
import json
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from zoneinfo import ZoneInfo

_BASE = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
LOCALE_DIR = _BASE / "locales"

DEFAULT_LANGUAGE = "en"
LANGUAGES = {"en": "English", "es": "Español", "fr": "Français", "hi": "हिन्दी", "ta": "தமிழ்"}
# Add right-to-left codes (e.g. "ar") here when such a locale ships; the page direction follows.
RTL_LANGUAGES = frozenset()

CATEGORIES = ["Groceries", "Furniture", "Meat & Seafood", "Electronics", "Clothing",
              "Hardware", "Pharmacy", "Stationery", "Bakery"]

# Country choice fixes the currency and time zone for a shop. Keys are ISO 3166-1 alpha-2 codes.
COUNTRIES = {
    "IN": {"name": "India", "currency": "INR", "timezone": "Asia/Kolkata"},
    "US": {"name": "United States", "currency": "USD", "timezone": "America/New_York"},
    "GB": {"name": "United Kingdom", "currency": "GBP", "timezone": "Europe/London"},
    "AE": {"name": "United Arab Emirates", "currency": "AED", "timezone": "Asia/Dubai"},
    "SG": {"name": "Singapore", "currency": "SGD", "timezone": "Asia/Singapore"},
    "AU": {"name": "Australia", "currency": "AUD", "timezone": "Australia/Sydney"},
    "FR": {"name": "France", "currency": "EUR", "timezone": "Europe/Paris"},
    "ES": {"name": "Spain", "currency": "EUR", "timezone": "Europe/Madrid"},
    "MX": {"name": "Mexico", "currency": "MXN", "timezone": "America/Mexico_City"},
}

CURRENCIES = {
    "INR": {"symbol": "₹", "decimals": 2},
    "USD": {"symbol": "$", "decimals": 2},
    "GBP": {"symbol": "£", "decimals": 2},
    "EUR": {"symbol": "€", "decimals": 2},
    "AED": {"symbol": "AED ", "decimals": 2},
    "SGD": {"symbol": "S$", "decimals": 2},
    "AUD": {"symbol": "A$", "decimals": 2},
    "MXN": {"symbol": "MX$", "decimals": 2},
}

# (decimal separator, thousands separator) by interface language.
NUMBER_SEPARATORS = {
    "en": (".", ","), "hi": (".", ","), "ta": (".", ","),
    "es": (",", "."), "fr": (",", " "),
}


def _load_translations():
    table = {}
    for code in LANGUAGES:
        if code == DEFAULT_LANGUAGE:
            continue
        path = LOCALE_DIR / f"{code}.json"
        table[code] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    return table


TRANSLATIONS = _load_translations()


def translate(text, lang=DEFAULT_LANGUAGE, **kwargs):
    value = TRANSLATIONS.get(lang, {}).get(text, text)
    return value.format(**kwargs) if kwargs else value


def resolve_language(requested=None, cookie=None, accept_match=None):
    """Priority: explicit ?lang= choice, remembered cookie, browser preference, English."""
    for candidate in (requested, cookie, accept_match):
        if candidate in LANGUAGES:
            return candidate
    return DEFAULT_LANGUAGE


def _group_western(digits, sep):
    parts = []
    while len(digits) > 3:
        parts.insert(0, digits[-3:])
        digits = digits[:-3]
    parts.insert(0, digits)
    return sep.join(parts)


def _group_indian(digits):
    """1234567 -> 12,34,567 (lakh/crore grouping used across India)."""
    if len(digits) <= 3:
        return digits
    head, tail = digits[:-3], digits[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts) + "," + tail


def format_money(amount, currency, lang=DEFAULT_LANGUAGE):
    """Format an amount in its own currency. Never mix currencies in one total."""
    info = CURRENCIES.get(currency, {"symbol": f"{currency} ", "decimals": 2})
    decimals = info["decimals"]
    quantum = Decimal(1).scaleb(-decimals)
    value = Decimal(str(amount or 0)).quantize(quantum, rounding=ROUND_HALF_UP)
    negative = value < 0
    int_part, _, frac = f"{abs(value):.{decimals}f}".partition(".")
    dec_sep, thou_sep = NUMBER_SEPARATORS.get(lang, NUMBER_SEPARATORS[DEFAULT_LANGUAGE])
    grouped = _group_indian(int_part) if currency == "INR" else _group_western(int_part, thou_sep)
    text = grouped + (dec_sep + frac if decimals else "")
    return ("-" if negative else "") + info["symbol"] + text


def to_local(value, tz_name):
    """Database timestamps are naive UTC. Convert them into the shop's time zone."""
    if value is None:
        return None
    from datetime import timezone
    aware = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
    try:
        zone = ZoneInfo(tz_name)
    except (ValueError, KeyError):
        zone = ZoneInfo("UTC")
    return aware.astimezone(zone)


def format_local(value, tz_name):
    local = to_local(value, tz_name)
    if local is None:
        return ""
    # Numeric date and 24-hour time avoid locale-dependent month names.
    return f"{local:%Y-%m-%d %H:%M} {local.tzname() or ''}".rstrip()
