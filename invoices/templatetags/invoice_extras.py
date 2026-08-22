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
