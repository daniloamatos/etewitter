
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from register.models import Usuario
from check.views import checkIfUsernameExists
from main.models import Tweet,Replys,SavedItems, Follower, Chat
from main.forms import replyForm,tweetForm
from main.views import generateLink
from main.targets import post_target
from django.db.models import Q
from django.db.models import Exists, OuterRef, Subquery
from django.core import serializers

def userprofile(request,username):
    followers = None
    following = None
    try:
        userprofileid = Usuario.objects.filter(username = username).values_list("id").all()

        um = Follower.objects.filter(follower_id__in = userprofileid).values_list("following_id").all()

        following = Usuario.objects.filter(id__in = um)

        dois = Follower.objects.filter(following_id__in = userprofileid).values_list("follower_id").all()

        followers = Usuario.objects.filter(id__in = dois)

    except:
        pass
    username = username
    if  checkIfUsernameExists(request, username):
        if request.method == "POST":
            if request.user.is_anonymous:
                return redirect('/login')
            form = tweetForm(request.POST, request.FILES)
            if form.is_valid() and (form.cleaned_data['tweet'] or form.cleaned_data['image']):
                simpanIp = form.save(commit=False)
                simpanIp.image = form.cleaned_data['image']
                simpanIp.tweetAuthor = request.user
                simpanIp.tweetLink = generateLink(request)
                simpanIp.save()
            else:
                messages.error(request, 'O tweet precisa haver algum caractere ou imagem.')
        else:
            form = tweetForm()
        jname = Usuario.objects.filter(username__iexact=username).values_list('name').first()
        user = Usuario.objects.get(username__iexact=username)
        checkUser = request.user
        retweeting_user = Usuario.objects.filter(
            retweets=OuterRef("pk"),
            pk=user.id,
        )
        tweets = Tweet.objects.filter(
            Q(tweetAuthor=user) | Q(retweets=user)
        ).annotate(
            retweet_by_name=Subquery(retweeting_user.values("name")[:1]),
            retweet_by_username=Subquery(retweeting_user.values("username")[:1]),
        ).distinct()
        reply_retweeters = Usuario.objects.filter(
            retweetsr=OuterRef("pk"), pk=user.id,
        )
        retweeted_replies = Replys.objects.filter(
            retweets=user,
        ).select_related("user", "tweet").annotate(
            retweet_by_name=Subquery(reply_retweeters.values("name")[:1]),
            retweet_by_username=Subquery(reply_retweeters.values("username")[:1]),
        ).prefetch_related("likes", "retweets").distinct()
        timeline = sorted(
            [*tweets, *retweeted_replies], key=lambda post: post.publishDate, reverse=True
        )
        return render(request, "userprofile/userprofile.html", {"followers":followers,"following":following, "form":form,"jusername":username, "jname":jname[0], "userP":user, "tweets":tweets, "retweeted_replies":retweeted_replies, "timeline": timeline, 'checkUser':checkUser, 'usuario':checkUser})
    else:
        return render(request, "userprofile/notexist.html")



@login_required(login_url='/login')
def likereply(request,**username):
    if request.method == 'POST':
        user = request.user
        reply_id = request.POST['replyid']
        reply_obj = get_object_or_404(Replys, id=reply_id)
        usuario = user
        liked = False
        if usuario not in reply_obj.likes.all():
            reply_obj.likes.add(usuario)
            reply_obj.likec += 1
            reply_obj.save()
            liked = True
            if reply_obj.user != user:
                from main.notifications import create_notification
                create_notification(
                    user=reply_obj.user,
                    actor=user,
                    notification_type='like',
                    body=f"{user.name} curtiu sua resposta",
                    linkzaocarai=reply_obj.replyLink,
                    reply=reply_obj,
                    tweet=reply_obj.tweet,
                )
        else:
            reply_obj.likes.remove(usuario)
            reply_obj.likec -= 1
            reply_obj.save()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'ok', 'liked': liked, 'count': reply_obj.likec})
        return HttpResponse(status=204)
    return redirect('/')

@login_required(login_url='/login')
def like (request, **username):
    if request.method == 'POST':
        user = request.user
        tweet_id = request.POST['tweetid']
        tweet_obj = get_object_or_404(Tweet, id=tweet_id)
        usuario = user
        liked = False
        if usuario not in tweet_obj.likes.all():
            tweet_obj.likes.add(usuario)
            tweet_obj.likec += 1
            tweet_obj.save()
            liked = True
            if tweet_obj.tweetAuthor != user:
                from main.notifications import create_notification
                create_notification(
                    user=tweet_obj.tweetAuthor,
                    actor=user,
                    notification_type='like',
                    body=f"{user.name} curtiu seu tweet",
                    linkzaocarai=tweet_obj.tweetLink,
                    tweet=tweet_obj,
                )
        else:
            tweet_obj.likes.remove(usuario)
            tweet_obj.likec -= 1
            tweet_obj.save()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'ok', 'liked': liked, 'count': tweet_obj.likec})
        return HttpResponse(status=204)
    return redirect('/')


@login_required(login_url='/login')
def retweet(request, **username):
    if request.method == 'POST':
        tweet_obj = get_object_or_404(Tweet, id=request.POST.get('tweetid'))
        retweeted = False
        if request.user in tweet_obj.retweets.all():
            tweet_obj.retweets.remove(request.user)
        else:
            tweet_obj.retweets.add(request.user)
            retweeted = True
            if tweet_obj.tweetAuthor != request.user:
                from main.notifications import create_notification
                create_notification(
                    user=tweet_obj.tweetAuthor,
                    actor=request.user,
                    notification_type='retweet',
                    body=f"{request.user.name} retweetou seu tweet",
                    linkzaocarai=tweet_obj.tweetLink,
                    tweet=tweet_obj,
                )
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'ok', 'retweeted': retweeted,
                'count': tweet_obj.retweets.count(),
            })
        return HttpResponse(status=204)
    return redirect('/')


@login_required(login_url='/login')
def retweetreply(request, **username):
    if request.method == 'POST':
        reply_obj = get_object_or_404(Replys, id=request.POST.get('replyid'))
        retweeted = False
        if request.user in reply_obj.retweets.all():
            reply_obj.retweets.remove(request.user)
        else:
            reply_obj.retweets.add(request.user)
            retweeted = True
            if reply_obj.user != request.user:
                from main.notifications import create_notification
                create_notification(
                    user=reply_obj.user,
                    actor=request.user,
                    notification_type='retweet',
                    body=f"{request.user.name} retweetou sua resposta",
                    linkzaocarai=reply_obj.replyLink,
                    reply=reply_obj,
                    tweet=reply_obj.tweet,
                )
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'ok', 'retweeted': retweeted,
                'count': reply_obj.retweets.count(),
            })
        return HttpResponse(status=204)
    return redirect('/')



@login_required(login_url='/login')
def reply (request, **username):
    if request.method == 'POST':
        reply = False
        user = request.user
        tweet_id = request.POST['tweetid']
        tweet_obj = (None if request.POST.get('content_type') == 'reply'
                     else Tweet.objects.filter(id=tweet_id).first())
        if tweet_obj is None:
            tweet_obj = get_object_or_404(Replys, id=tweet_id)
            reply = True
        form = replyForm(request.POST, request.FILES)
        if form.is_valid() and (form.cleaned_data['body'] or form.cleaned_data['image']):
            if reply:

                test = Replys.objects.create(
                    user = user,
                    tweet = tweet_obj.tweet,
                    body = form.cleaned_data['body'],
                    image = form.cleaned_data['image'],
                    replyLink = generateLink(request)
                )
                test.reply.add(tweet_obj)
                tweet_obj.replysC += 1
                tweet_obj.save(update_fields=['replysC'])
                if tweet_obj.user != user:
                    from main.notifications import create_notification
                    create_notification(
                        user=tweet_obj.user,
                        actor=user,
                        notification_type='reply',
                        body=f"{user.name} respondeu à sua publicação",
                        linkzaocarai=test.replyLink,
                        reply=test,
                        tweet=tweet_obj.tweet,
                    )
                return redirect(request.POST.get('next', '/'))
            else:
                instance = form.save(commit=False)
                instance.tweet = tweet_obj
                instance.image = form.cleaned_data['image']
                tweet_obj.replysC += 1
                tweet_obj.save()
                instance.user = user
                instance.body = request.POST['body']
                instance.replyLink = generateLink(request)
                instance.save()
                if tweet_obj.tweetAuthor != user:
                    from main.notifications import create_notification
                    create_notification(
                        user=tweet_obj.tweetAuthor,
                        actor=user,
                        notification_type='reply',
                        body=f"{user.name} respondeu ao seu tweet",
                        linkzaocarai=instance.replyLink,
                        reply=instance,
                        tweet=tweet_obj,
                    )
                return redirect(request.POST.get('next', '/'))
        else:
            messages.error(request, 'O tweet precisa haver algum caractere ou imagem.')
    return redirect(request.POST.get('next', '/'))


def requesttweet (request, username, random):
    checkUser = request.user
    form = replyForm()
    if Tweet.objects.filter(tweetLink=f'{username}/status/{random}'):
        tweet = Tweet.objects.filter(tweetLink=f'{username}/status/{random}')
        tweetObj = Tweet.objects.get(tweetLink=f'{username}/status/{random}')
        child_reply = Replys.objects.filter(
            reply=OuterRef('pk'),
            publishDate__gt=OuterRef('publishDate'),
        )
        qs = Replys.objects.filter(
            tweet=tweet[0],
            reply__isnull=True,
        ).annotate(has_children=Exists(child_reply))
        notReply = True
        mentionLink = Tweet.objects.filter(
            tweetLink=f'{username}/status/{random}'
        ).values_list('mentionlink', flat=True).first()
        if mentionLink:
            return render(request, "userprofile/tweet.html", {'tweet':tweet, 'usuario':checkUser, 'form':form, 'qs':qs, 'notReply':notReply, 'tweetObj':tweetObj, 'mentionlink':mentionLink})
        return render(request, "userprofile/tweet.html", {'tweet':tweet, 'usuario':checkUser, 'form':form, 'qs':qs, 'notReply':notReply, 'tweetObj':tweetObj})
    else:
        notReply = False
        reply = Replys.objects.filter(replyLink=f'{username}/status/{random}')
        if not reply.exists():
            return render(request, "userprofile/notexist.html", status=404)
        tweetObj = reply.first()
        parent_replies = []
        parent = tweetObj.reply.filter(
            publishDate__lt=tweetObj.publishDate
        ).order_by('-publishDate').first()
        visited = {tweetObj.pk}
        while parent and parent.pk not in visited:
            parent_replies.append(parent)
            visited.add(parent.pk)
            parent = parent.reply.filter(
                publishDate__lt=parent.publishDate
            ).order_by('-publishDate').first()
        parent_replies.reverse()
        child_reply = Replys.objects.filter(
            reply=OuterRef('pk'),
            publishDate__gt=OuterRef('publishDate'),
        )
        qs = Replys.objects.filter(
            reply=tweetObj,
            publishDate__gt=tweetObj.publishDate,
        ).exclude(pk__in=visited).annotate(has_children=Exists(child_reply))
        return render(request, "userprofile/tweet.html", {
            'tweet': reply,
            'usuario': checkUser,
            'form': form,
            'qs': qs,
            'notReply': notReply,
            'tweetObj': tweetObj,
            'parent_replies': parent_replies,
        })

@login_required(login_url='/login')
def save(request):
    if request.method == 'POST':
        user = request.user
        kind, target = post_target(request)
        lookup = {'user': user, kind: target}
        saveditems = SavedItems.objects.filter(**lookup)
        action = request.POST.get('action', 'toggle')
        if action == 'remove' or (action == 'toggle' and saveditems.exists()):
            saveditems.delete()
            saved = False
        elif action in ('save', 'toggle'):
            SavedItems.objects.get_or_create(**lookup)
            saved = True
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'ok', 'saved': saved})
        return HttpResponse(status=204)
    return redirect('/')

@login_required(login_url='/login')
def message(request):
    user = request.user
    conversation = Chat.objects.filter(Q(sender=user) | Q(receiver=user))
    return render(request, 'main/message.html', {'chats':conversation})
