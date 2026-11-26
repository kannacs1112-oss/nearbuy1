"""Internationalisation rules and translation coverage.

These tests deliberately import only intl.py, so they run without Flask or SQLAlchemy.
They fail if a new UI string is added to a template or app.py without a translation.
"""
import json
import re
import string
from datetime import datetime
from pathlib import Path

import pytest

import intl

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_KEY = re.compile(r"""_\(\s*(?:"((?:[^"\\]|\\.)*)"|'((?:[^'\\]|\\.)*)')""")

# Strings the templates and app.py show by way of a variable, not a literal _() call.
DYNAMIC_KEYS = (
    list(intl.CATEGORIES)
    + list(intl.COUNTRIES[code]["name"] for code in intl.COUNTRIES)
    + ["Placed", "Confirmed", "Preparing", "Ready for pickup", "Out for delivery",
       "Delivered", "Cancelled"]
    + ["Very low stock", "Likely to run low", "No recorded sales", "Stock looks healthy"]
    + ["piece", "kg", "litre", "pack", "kit"]
)


def _ui_strings():
    keys = set(DYNAMIC_KEYS)
    for path in list((ROOT / "templates").glob("*.html")) + [ROOT / "app.py"]:
        for match in TEMPLATE_KEY.finditer(path.read_text(encoding="utf-8")):
            keys.add((match.group(1) or match.group(2)).replace("\\'", "'"))
    return keys


def _placeholders(text):
    return {field for _, field, _, _ in string.Formatter().parse(text) if field}


def _catalogue(code):
    return json.loads((ROOT / "locales" / f"{code}.json").read_text(encoding="utf-8"))


TRANSLATED = [code for code in intl.LANGUAGES if code != intl.DEFAULT_LANGUAGE]


@pytest.mark.parametrize("code", TRANSLATED)
def test_every_ui_string_is_translated(code):
    catalogue = _catalogue(code)
    missing = sorted(_ui_strings() - set(catalogue))
    assert not missing, f"{code} is missing {len(missing)} strings, e.g. {missing[:5]}"


@pytest.mark.parametrize("code", TRANSLATED)
def test_translations_keep_placeholders(code):
    catalogue = _catalogue(code)
    broken = [key for key, value in catalogue.items()
              if _placeholders(key) != _placeholders(value)]
    assert not broken, f"{code} changes placeholders in: {broken[:5]}"


@pytest.mark.parametrize("code", TRANSLATED)
def test_no_empty_translations(code):
    empty = [key for key, value in _catalogue(code).items() if not value.strip()]
    assert not empty, f"{code} has empty values for: {empty[:5]}"


def test_templates_parse():
    jinja2 = pytest.importorskip("jinja2")
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(ROOT / "templates")))
    for path in (ROOT / "templates").glob("*.html"):
        env.parse(path.read_text(encoding="utf-8"))


# ----- money -----

def test_inr_uses_lakh_grouping():
    assert intl.format_money(1234567, "INR", "en") == "₹12,34,567.00"
    assert intl.format_money(100000, "INR", "hi") == "₹1,00,000.00"
    assert intl.format_money(999, "INR") == "₹999.00"


def test_usd_uses_western_grouping_and_two_decimals():
    assert intl.format_money(1234.5, "USD", "en") == "$1,234.50"


def test_spanish_and_french_separators_follow_the_interface_language():
    assert intl.format_money(1234.5, "EUR", "es") == "€1.234,50"
    assert intl.format_money(1234.5, "EUR", "fr") == "€1 234,50"


def test_rounding_is_half_up_not_bankers():
    assert intl.format_money("2.675", "USD") == "$2.68"
    assert intl.format_money("0.005", "USD") == "$0.01"


def test_negative_amounts_and_unknown_currency():
    assert intl.format_money(-5, "USD") == "-$5.00"
    assert intl.format_money(10, "XYZ").startswith("XYZ ")


def test_money_is_never_summed_across_currencies():
    # Guard the helper's contract: it formats one currency at a time.
    assert intl.format_money(100, "INR") != intl.format_money(100, "USD")


# ----- time zones -----

def test_stored_utc_is_shown_in_shop_time_zone():
    stored = datetime(2026, 11, 25, 9, 35)  # naive UTC, as the database stores it
    assert intl.format_local(stored, "Asia/Kolkata") == "2026-11-25 15:05 IST"


def test_format_is_numeric_and_locale_independent():
    text = intl.format_local(datetime(2026, 1, 2, 0, 0), "America/New_York")
    assert text.startswith("2026-01-01 19:00")


def test_bad_zone_name_falls_back_to_utc():
    assert intl.format_local(datetime(2026, 1, 2, 0, 0), "Not/AZone").startswith("2026-01-02 00:00")


def test_missing_timestamp_is_empty():
    assert intl.format_local(None, "Asia/Kolkata") == ""


def test_every_country_has_a_valid_zone_and_currency():
    for code, info in intl.COUNTRIES.items():
        assert info["currency"] in intl.CURRENCIES, code
        intl.to_local(datetime(2026, 1, 1), info["timezone"])  # raises if invalid


# ----- language choice and translation -----

def test_explicit_choice_beats_cookie_beats_browser():
    assert intl.resolve_language("fr", "es", "hi") == "fr"
    assert intl.resolve_language(None, "es", "hi") == "es"
    assert intl.resolve_language(None, None, "ta") == "ta"


def test_unsupported_values_fall_back_to_english():
    assert intl.resolve_language("xx", "yy", None) == intl.DEFAULT_LANGUAGE
    assert intl.resolve_language(None, None, None) == intl.DEFAULT_LANGUAGE


def test_translate_falls_back_and_formats():
    assert intl.translate("Cart", "fr") == "Panier"
    assert intl.translate("Something new", "fr") == "Something new"
    assert intl.translate("Hey, {name}", "en", name="Asha") == "Hey, Asha"
    assert intl.translate("Hey, {name}", "hi", name="Asha") == "नमस्ते, Asha"
