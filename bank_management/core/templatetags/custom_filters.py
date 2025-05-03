from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def subtract(value, arg):
    """Subtract the arg from the value."""
    try:
        return value - arg
    except (ValueError, TypeError):
        try:
            return Decimal(str(value)) - Decimal(str(arg))
        except:
            return value

@register.filter
def divide(value, arg):
    """Divide the value by the arg."""
    try:
        return value / arg
    except (ValueError, TypeError, ZeroDivisionError):
        try:
            if arg != 0:
                return Decimal(str(value)) / Decimal(str(arg))
            return 0
        except:
            return 0

@register.filter
def multiply(value, arg):
    """Multiply the value by the arg."""
    try:
        return value * arg
    except (ValueError, TypeError):
        try:
            return Decimal(str(value)) * Decimal(str(arg))
        except:
            return 0