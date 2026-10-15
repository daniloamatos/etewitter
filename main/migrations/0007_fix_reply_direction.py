from django.db import migrations


def remove_reverse_reply_links(apps, schema_editor):
    Replys = apps.get_model('main', 'Replys')
    for reply in Replys.objects.prefetch_related('reply').all():
        for parent in reply.reply.all():
            if parent.publishDate >= reply.publishDate:
                reply.reply.remove(parent)


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0006_notification_linkzaocarai'),
    ]

    operations = [
        migrations.RunPython(
            remove_reverse_reply_links,
            migrations.RunPython.noop,
        ),
    ]
