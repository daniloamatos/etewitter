

import random
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from .forms import tweetForm
from .image_utils import form_image_errors
from .targets import post_target
from asgiref.sync import async_to_sync
from .models import Replys, Tweet, SavedItems as SavedItemsclass, Follower, Message, Report, Notification
from register.models import Usuario
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.db.models import OuterRef, Q, Subquery
# Create your views here.



@login_required(login_url='/login')
def notifications(request):
    user = request.user
    notifications_qs = Notification.objects.filter(user=user).exclude(
        linkzaocarai__startswith='messages/'
    ).select_related(
        "actor",
        "tweet",
        "tweet__tweetAuthor",
        "reply",
        "reply__user",
        "reply__tweet",
        "reply__tweet__tweetAuthor",
    ).order_by("-id")
    Notification.objects.filter(user=user, is_read=False).update(is_read=True)
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                user.username + 'notifications',
                {
                    'type': 'unread_notifications',
                    'unread': False,
                }
            )
    except Exception:
        pass
    return render(request, 'main/notifications.html', {'user':user,'notifications':notifications_qs})

@login_required(login_url='/login')
def home(request):
    users = Usuario.objects.all()
    for user in users:
        user.username = '@' + user.username
    tweets_self = Tweet.objects.filter(tweetAuthor=request.user)
    following = Follower.objects.filter(
        follower_id=request.user.id
    ).values_list("following_id", flat=True)
    visible_retweeters = Usuario.objects.filter(
        retweets=OuterRef("pk"),
        pk__in=list(following) + [request.user.id],
    )
    tweets = Tweet.objects.filter(
        Q(tweetAuthor=request.user)
        | Q(tweetAuthor_id__in=following)
        | Q(retweets__in=list(following) + [request.user.id])
    ).annotate(
        retweet_by_name=Subquery(visible_retweeters.values("name")[:1]),
        retweet_by_username=Subquery(visible_retweeters.values("username")[:1]),
    ).distinct()
    reply_retweeters = Usuario.objects.filter(
        retweetsr=OuterRef("pk"), pk__in=list(following) + [request.user.id],
    )
    retweeted_replies = Replys.objects.filter(
        retweets__in=list(following) + [request.user.id],
    ).select_related("user", "tweet").annotate(
        retweet_by_name=Subquery(reply_retweeters.values("name")[:1]),
        retweet_by_username=Subquery(reply_retweeters.values("username")[:1]),
    ).prefetch_related("likes", "retweets").distinct()
    timeline = sorted(
        [*tweets, *retweeted_replies], key=lambda post: post.publishDate, reverse=True
    )
    if request.method == "POST":
        form = tweetForm(request.POST, request.FILES)
        if form.is_valid() and (form.cleaned_data['tweet'] or form.cleaned_data['image']):
            tweet = form.save(commit=False)
            tweet.tweetAuthor = request.user
            tweet.tweetLink = generateLink(request)
            mention = next(
                (word[1:] for word in tweet.tweet.split() if word.startswith('@')),
                None,
            )
            if mention:
                tweet.mentionlink = mention + "/"
            tweet.save()
            if mention:
                mentioned_user = Usuario.objects.filter(username__iexact=mention).first()
                if mentioned_user:
                    from .notifications import create_notification
                    create_notification(
                        user=mentioned_user,
                        actor=request.user,
                        notification_type='mention',
                        body=f"{request.user.name} te mencionou em um tweet",
                        linkzaocarai=tweet.tweetLink,
                        tweet=tweet,
                    )
            return redirect("/")
        errors = form_image_errors(form)
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            messages.error(request, 'O tweet precisa haver algum caractere ou imagem.')
    else:
        form = tweetForm()
    usuario = Usuario.objects.get(username=request.user.username)
    return render(request, "main/homepage.html", {
        "form": form, "tweets": tweets, "retweeted_replies": retweeted_replies, "timeline": timeline,
        'usuario': usuario, "users": users
    })

def index(request):
    if request.user.is_authenticated:
        return redirect('/')
    else:
        return render(request, "main/index.html", {})

def generateLink(request):
    chars = '1234567890'
    randomstr = ''.join((random.choice(chars)) for x in range(30))
    _now = datetime.now()
    day=_now.strftime('%d')
    month=_now.strftime('%m')
    year=_now.strftime('%Y')
    link = str(f'{request.user.username}/status/{randomstr}{day}{month}{year}')
    return link

@login_required(login_url='/login')
def saveditems(request):
    user = request.user
    tweet = SavedItemsclass.objects.filter(user=user).select_related("tweet__tweetAuthor", "reply__user").order_by("-id")
    return render(request, 'main/saveditems.html', {'user':user, 'tweet':tweet})


@login_required(login_url='/login')
def follow(request):
    if request.method == 'POST':
        user = request.user
        following = get_object_or_404(Usuario, id=request.POST.get('userP'))
        next_url = request.POST.get('next', '/')
        if following == user:
            messages.error(request, 'Você não pode seguir a si mesmo.')
        elif Follower.objects.filter(following_id=following.id, follower=user.id).exists():
            Follower.objects.filter(follower = user, following = following).delete()
            following.followersC -=1
            following.save()
            user.followingC -= 1
            user.save()
            return redirect(next_url)
        else:
            Follower.objects.create(follower = user, following = following)
            following.followersC +=1
            following.save()
            user.followingC += 1
            user.save()
            if following != user:
                from .notifications import create_notification
                create_notification(
                    user=following,
                    actor=user,
                    notification_type='follow',
                    body=f"{user.name} começou a te seguir",
                    linkzaocarai=f"{user.username}/",
                )
            return redirect(next_url)
    return redirect('/')

def sendmessage(request, sender, receiver, message, next):
    if request.method == 'POST':
        Message.objects.create(
            sender = sender,
            receiver = receiver,
            body = message
        )
        return redirect(next)

@login_required(login_url='/login')
def delete(request):
    if request.method == "POST":
        next_url = request.POST.get('next', '/')
        if request.POST.get('content_type') == 'reply':
            reply = get_object_or_404(Replys, id=request.POST.get('tweetid'))
            if reply.user_id != request.user.id:
                messages.error(request, 'Você não pode deletar esta resposta.')
                return redirect(next_url)
            for child in Replys.objects.filter(tweet=reply.tweet, reply=reply):
                child.reply.remove(reply)
            reply.delete()
            messages.success(request, 'Resposta deletada.')
            return redirect(next_url)

        tweet = get_object_or_404(Tweet, id=request.POST.get('tweetid'))
        if tweet.tweetAuthor_id != request.user.id:
            messages.error(request, 'Você não pode deletar este tweet.')
            return redirect(next_url)
        tweet.delete()
        messages.success(request, 'Tweet deletado.')
        return redirect(next_url)

@login_required(login_url='/login')
def report(request):
    if request.method == 'POST':
        kind, target = post_target(request)
        author_id = target.user_id if kind == 'reply' else target.tweetAuthor_id
        if author_id == request.user.id:
            return HttpResponseForbidden('Você não pode denunciar sua própria publicação.')
        reason = request.POST.get('reason', '').strip()
        if reason and len(reason) <= 100:
            Report.objects.create(x9=request.user, reason=reason, **{kind: target})
            messages.success(request, 'Denuncia registrada.')
        else:
            messages.error(request, 'Informe um motivo de até 100 caracteres.')
        return redirect(request.POST.get('next', '/'))
    return redirect('/')
