import re
from decimal import Decimal

from django import template

register = template.Library()


@register.filter(name="trim_decimal")
def trim_decimal(value: Decimal | str | float | None) -> str:
    if value is None or value == "":
        return ""

    number = Decimal(str(value)).quantize(Decimal("0.01"))
    formatted = f"{number:.2f}".rstrip("0").rstrip(".")
    return formatted or "0"


@register.filter(name="strip_scheme")
def strip_scheme(url: str | None) -> str:
    if not url:
        return ""

    url = re.sub(r"^https?://", "", url)
    return url.rstrip("/")


CURRENCY_SYMBOLS = {
    "INR": "₹",
    "USD": "$",
}


@register.filter(name="currency_symbol")
def currency_symbol(code: str | None) -> str:
    if not code:
        return ""
    code = code.upper()
    return CURRENCY_SYMBOLS.get(code, code)


@register.filter(name="pluralize_unit")
def pluralize_unit(unit_type: str, quantity):
    if not unit_type or unit_type == "QTY":
        return ""

    labels = {"HRS": "Hour", "DAYS": "Day"}
    label = labels.get(unit_type, unit_type)

    try:
        qty = Decimal(str(quantity))
    except Exception:
        qty = Decimal("1")

    if qty == 1:
        return label

    return f"{label}s"
