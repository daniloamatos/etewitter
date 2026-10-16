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


@register.filter
def render_mentions(value):
    """Escape user content before inserting links; unknown handles stay plain text."""
    from django.utils.html import escape, format_html
    from django.utils.safestring import mark_safe
    from main.mentions import MENTION_RE, mentioned_users

    text = str(value or '')
    users = mentioned_users(text)
    parts = []
    offset = 0
    for match in MENTION_RE.finditer(text):
        parts.append(str(escape(text[offset:match.start()])))
        user = users.get(match.group(1).lower())
        parts.append(str(format_html(
            '<a class="profile-handle-link mention-link" href="/{}/">{}</a>',
            user.username, match.group(),
        )) if user else str(escape(match.group())))
        offset = match.end()
    parts.append(str(escape(text[offset:])))
    return mark_safe(''.join(parts).replace('\r\n', '\n').replace('\r', '\n').replace('\n', '<br>'))
