from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def preserve_existing_retweets(apps, schema_editor):
    Tweet = apps.get_model('main', 'Tweet')
    Replys = apps.get_model('main', 'Replys')
    TweetRetweet = apps.get_model('main', 'TweetRetweet')
    ReplyRetweet = apps.get_model('main', 'ReplyRetweet')
    db = schema_editor.connection.alias

    # The old join tables had no retweet time. The original post time is the
    # only available value, so existing entries retain their previous order.
    tweet_dates = dict(Tweet.objects.using(db).values_list('pk', 'publishDate'))
    tweet_events = [
        TweetRetweet(tweet_id=relation.tweet_id, user_id=relation.usuario_id,
                     created_at=tweet_dates[relation.tweet_id])
        for relation in Tweet.retweets.through.objects.using(db).all().iterator()
    ]
    TweetRetweet.objects.using(db).bulk_create(tweet_events, batch_size=500)

    reply_dates = dict(Replys.objects.using(db).values_list('pk', 'publishDate'))
    reply_events = [
        ReplyRetweet(reply_id=relation.replys_id, user_id=relation.usuario_id,
                     created_at=reply_dates[relation.replys_id])
        for relation in Replys.retweets.through.objects.using(db).all().iterator()
    ]
    ReplyRetweet.objects.using(db).bulk_create(reply_events, batch_size=500)


def restore_old_join_tables(apps, schema_editor):
    Tweet = apps.get_model('main', 'Tweet')
    Replys = apps.get_model('main', 'Replys')
    TweetRetweet = apps.get_model('main', 'TweetRetweet')
    ReplyRetweet = apps.get_model('main', 'ReplyRetweet')
    db = schema_editor.connection.alias
    Tweet.retweets.through.objects.using(db).bulk_create([
        Tweet.retweets.through(tweet_id=event.tweet_id, usuario_id=event.user_id)
        for event in TweetRetweet.objects.using(db).all().iterator()
    ], batch_size=500)
    Replys.retweets.through.objects.using(db).bulk_create([
        Replys.retweets.through(replys_id=event.reply_id, usuario_id=event.user_id)
        for event in ReplyRetweet.objects.using(db).all().iterator()
    ], batch_size=500)


class Migration(migrations.Migration):

    dependencies = [('main', '0003_alter_message_body_alter_message_image')]

    operations = [
        migrations.CreateModel(
            name='TweetRetweet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('tweet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='retweet_events', to='main.tweet')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ReplyRetweet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('reply', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='retweet_events', to='main.replys')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name='tweetretweet',
            constraint=models.UniqueConstraint(fields=('tweet', 'user'), name='unique_tweet_retweet'),
        ),
        migrations.AddConstraint(
            model_name='replyretweet',
            constraint=models.UniqueConstraint(fields=('reply', 'user'), name='unique_reply_retweet'),
        ),
        migrations.RunPython(preserve_existing_retweets, restore_old_join_tables),
        migrations.RemoveField(model_name='tweet', name='retweets'),
        migrations.RemoveField(model_name='replys', name='retweets'),
        migrations.AddField(
            model_name='tweet', name='retweets',
            field=models.ManyToManyField(blank=True, related_name='retweets', through='main.TweetRetweet', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='replys', name='retweets',
            field=models.ManyToManyField(blank=True, related_name='retweetsr', through='main.ReplyRetweet', to=settings.AUTH_USER_MODEL),
        ),
    ]
