from main.mentions import register_mentions
from main.notifications import notify_post_interaction

from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils.translation import gettext as _
from register.models import Usuario
from check.views import checkIfUsernameExists
from main.models import Tweet,Replys,SavedItems, Follower, Chat, Message
from main.forms import replyForm,tweetForm
from main.image_utils import form_image_errors
from main.views import generateLink
from main.targets import post_target
from main.timeline import build_timeline
from django.db.models import Q
from django.db.models import Exists, OuterRef
from django.core import serializers
from django.templatetags.static import static


def profile_preview(request, username):
    person = get_object_or_404(Usuario, username__iexact=username)
    viewer = request.user
    authenticated = viewer.is_authenticated
    following = authenticated and Follower.objects.filter(
        follower=viewer, following=person
    ).exists()
    follows_you = authenticated and Follower.objects.filter(
        follower=person, following=viewer
    ).exists()
    picture = (person.profilepic.url if person.profilepic and
               person.profilepic.name != 'default/default_profile_400x400.png'
               else static('images/default-profile.svg'))
    return JsonResponse({
        'id': str(person.pk), 'name': person.name, 'username': person.username,
        'bio': person.bio, 'picture': picture,
        'followers': person.followersC, 'following': person.followingC,
        'is_self': authenticated and person.pk == viewer.pk,
        'is_following': following, 'follows_you': follows_you,
        'authenticated': authenticated,
    })

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
                register_mentions(simpanIp)
            else:
                errors = form_image_errors(form)
                if errors:
                    for error in errors:
                        messages.error(request, error)
                else:
                    messages.error(request, _('O tweet precisa haver algum caractere ou imagem.'))
        else:
            form = tweetForm()
        jname = Usuario.objects.filter(username__iexact=username).values_list('name').first()
        user = Usuario.objects.get(username__iexact=username)
        checkUser = request.user
        tweets, retweeted_replies, timeline = build_timeline([user.id], [user.id])
        follows_you = request.user.is_authenticated and Follower.objects.filter(
            follower=user, following=request.user
        ).exists()
        return render(request, "userprofile/userprofile.html", {"followers":followers,"following":following, "follows_you": follows_you, "form":form,"jusername":username, "jname":jname[0], "userP":user, "tweets":tweets, "retweeted_replies":retweeted_replies, "timeline": timeline, 'checkUser':checkUser, 'usuario':checkUser})
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
            notify_post_interaction(reply_obj, request.user, 'like')
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
            notify_post_interaction(tweet_obj, request.user, 'like')
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
            notify_post_interaction(tweet_obj, request.user, 'retweet')
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
            notify_post_interaction(reply_obj, request.user, 'retweet')
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
                from main.notifications import notify_reply_thread
                register_mentions(test)
                notify_reply_thread(test, tweet_obj)
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
                from main.notifications import notify_reply_thread
                register_mentions(instance)
                notify_reply_thread(instance, tweet_obj)
                return redirect(request.POST.get('next', '/'))
        else:
            errors = form_image_errors(form)
            if errors:
                for error in errors:
                    messages.error(request, error)
            else:
                messages.error(request, _('O tweet precisa haver algum caractere ou imagem.'))
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
    chats = Chat.objects.filter(Q(sender=user) | Q(receiver=user)).select_related(
        'sender', 'receiver'
    ).order_by('-publishDate')
    conversations = []
    seen = set()
    for chat in chats:
        peer = chat.receiver if chat.sender_id == user.id else chat.sender
        if peer.id in seen:
            continue
        seen.add(peer.id)
        last = Message.objects.filter(
            Q(sender=user, receiver=peer) | Q(sender=peer, receiver=user)
        ).order_by('-publishDate', '-id').first()
        conversations.append({
            'peer': peer,
            'last': last,
            'mine': bool(last and last.sender_id == user.id),
        })
    return render(request, 'main/message.html', {'conversations': conversations})
