from decimal import Decimal

from django import template

register = template.Library()


@register.filter(name="trim_decimal")
def trim_decimal(value: Decimal | float | str | None) -> str:
    """Format a number to 2 decimal places, stripping trailing zeros.

    4.00 -> "4", 4.50 -> "4.5", 4.35 -> "4.35"
    """
    if value is None:
        return ""

    number = Decimal(str(value)).quantize(Decimal("0.01"))
    formatted = f"{number:.2f}".rstrip("0").rstrip(".")
    return formatted or "0"
