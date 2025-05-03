from django import template

register = template.Library()

@register.filter
def subtract(value, arg):
    """Subtracts the arg from the value."""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def divide(value, arg):
    """Divides the value by the arg."""
    try:
        arg = float(arg)
        if arg == 0:
            return 0
        return float(value) / arg
    except (ValueError, TypeError):
        return value

@register.filter
def multiply(value, arg):
    """Multiplies the value by the arg."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return value