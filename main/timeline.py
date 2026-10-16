from .models import ReplyRetweet, Replys, Tweet, TweetRetweet


def build_timeline(author_ids, retweeter_ids):
    """Return original tweets and individual retweet entries in event order."""
    tweets = list(Tweet.objects.filter(tweetAuthor_id__in=author_ids).select_related('tweetAuthor'))
    for tweet in tweets:
        tweet.timeline_date = tweet.publishDate

    retweeted_replies = []
    timeline = list(tweets)
    for event in TweetRetweet.objects.filter(user_id__in=retweeter_ids).select_related(
        'tweet', 'tweet__tweetAuthor', 'user'
    ):
        tweet = event.tweet
        tweet.retweet_by_name = event.user.name
        tweet.retweet_by_username = event.user.username
        tweet.retweet_date = event.created_at
        tweet.timeline_date = event.created_at
        timeline.append(tweet)

    reply_events = list(ReplyRetweet.objects.filter(user_id__in=retweeter_ids).select_related(
        'reply', 'reply__user', 'reply__tweet', 'user'
    ))
    parent_ids = set(Replys.objects.filter(
        reply__in=[event.reply_id for event in reply_events]
    ).values_list('reply', flat=True).distinct())
    for event in reply_events:
        reply = event.reply
        reply.has_children = reply.pk in parent_ids
        reply.retweet_by_name = event.user.name
        reply.retweet_by_username = event.user.username
        reply.retweet_date = event.created_at
        reply.timeline_date = event.created_at
        retweeted_replies.append(reply)
        timeline.append(reply)

    timeline.sort(key=lambda post: post.timeline_date, reverse=True)
    return tweets, retweeted_replies, timeline
