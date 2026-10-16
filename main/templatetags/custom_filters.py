from django import template
from django.utils import timezone

register = template.Library()


@register.filter
def smart_date(value):
    """
    Retorna a data no formato DD/MM se for do ano atual,
    e DD/MM/YYYY se for de outro ano.
    """
    if value is None:
        return ''
    try:
        # Garante que value seja um datetime/date consciente (aware)
        if timezone.is_naive(value):
            value = timezone.make_aware(value, timezone.get_current_timezone())
    except Exception:
        return value
    now = timezone.localtime()
    if value.year == now.year:
        return value.strftime('%d/%m')
    return value.strftime('%d/%m/%Y')
