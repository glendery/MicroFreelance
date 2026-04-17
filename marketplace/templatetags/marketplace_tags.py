from django import template

register = template.Library()

@register.filter(name='rupiah')
def rupiah(value):
    try:
        # Format: Rp 1.000.000
        return f"Rp {int(value):,}".replace(',', '.')
    except (ValueError, TypeError):
        return value
