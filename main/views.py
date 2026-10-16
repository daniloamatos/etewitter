

import random
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.conf import settings
from .forms import tweetForm
from .image_utils import form_image_errors
from .targets import post_target
from .timeline import build_timeline
from asgiref.sync import async_to_sync
from .models import Replys, Tweet, SavedItems as SavedItemsclass, Follower, Message, Report, Notification
from register.models import Usuario
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _, check_for_language
from django.views.decorators.http import require_POST
from datetime import datetime
from django.db.models import Exists, OuterRef, Q
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
    ).prefetch_related(
        'tweet__likes', 'tweet__retweets', 'reply__likes', 'reply__retweets',
        'reply__reply__user',
    ).order_by("-publishDate", "-id")
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
def notification_card(request, notification_id):
    notification = get_object_or_404(
        Notification.objects.select_related('actor', 'tweet', 'reply', 'reply__tweet__tweetAuthor').prefetch_related('reply__reply__user'),
        pk=notification_id,
        user=request.user,
    )
    return render(request, 'main/notification_card.html', {'notification': notification})


def reply_children(request, reply_id):
    try:
        parent_depth = min(max(int(request.GET.get('depth', 0)), 0), 1)
    except (TypeError, ValueError):
        parent_depth = 0
    parent = get_object_or_404(Replys, pk=reply_id)
    child_reply = Replys.objects.filter(reply=OuterRef('pk'))
    children = Replys.objects.filter(reply=parent).select_related(
        'user', 'tweet', 'tweet__tweetAuthor',
    ).annotate(has_children=Exists(child_reply)).order_by('-publishDate')
    return render(request, 'main/reply_children.html', {
        'parent': parent,
        'children': children,
        'expand_depth': parent_depth + 1,
        'hide_expand_buttons': parent_depth + 1 >= 2,
    })


@login_required(login_url='/login')
def mention_suggestions(request):
    """Suggest followed accounts for the handle being typed."""
    query = request.GET.get('q', '').lstrip('@')[:25]
    if query and not query.isascii():
        return JsonResponse({'users': []})
    followed = Usuario.objects.filter(
        userFollowing__follower=request.user,
    )
    if query:
        followed = followed.filter(Q(username__icontains=query) | Q(name__icontains=query))
    users = followed.order_by('username').distinct()[:8]
    return JsonResponse({'users': [
        {'username': user.username, 'name': user.name,
         'avatar': user.profilepic.url if user.profilepic and user.profilepic.name != 'default/default_profile_400x400.png' else settings.STATIC_URL + 'images/default-profile.svg'}
        for user in users
    ]})

@login_required(login_url='/login')
def home(request):
    users = Usuario.objects.all()
    for user in users:
        user.username = '@' + user.username
    following = Follower.objects.filter(
        follower_id=request.user.id
    ).values_list("following_id", flat=True)
    visible_users = list(following) + [request.user.id]
    tweets, retweeted_replies, timeline = build_timeline(visible_users, visible_users)
    if request.method == "POST":
        form = tweetForm(request.POST, request.FILES)
        if form.is_valid() and (form.cleaned_data['tweet'] or form.cleaned_data['image']):
            tweet = form.save(commit=False)
            tweet.tweetAuthor = request.user
            tweet.tweetLink = generateLink(request)
            tweet.save()
            from .mentions import register_mentions
            register_mentions(tweet)
            return redirect("/")
        errors = form_image_errors(form)
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            messages.error(request, _('O tweet precisa haver algum caractere ou imagem.'))
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


@require_POST
def set_language(request):
    """Troca o idioma ativo guardando a escolha num cookie.

    Feito à mão em vez de ``django.conf.urls.i18n.set_language`` porque neste
    projeto as mesmas URLs são incluídas em vários prefixos e o
    ``translate_url`` usado pelo Django reescrevia o destino para o lugar
    errado (ex.: ``/index/`` virava ``/notifications/index/``).
    """
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or '/'
    if not url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = '/'
    response = HttpResponseRedirect(next_url)
    lang_code = request.POST.get('language', '')
    if lang_code and check_for_language(lang_code):
        response.set_cookie(
            settings.LANGUAGE_COOKIE_NAME,
            lang_code,
            max_age=settings.LANGUAGE_COOKIE_AGE,
            path=settings.LANGUAGE_COOKIE_PATH,
            domain=settings.LANGUAGE_COOKIE_DOMAIN,
            secure=settings.LANGUAGE_COOKIE_SECURE,
            httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
            samesite=settings.LANGUAGE_COOKIE_SAMESITE,
        )
    return response

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
            messages.error(request, _('Você não pode seguir a si mesmo.'))
        elif Follower.objects.filter(following_id=following.id, follower=user.id).exists():
            Follower.objects.filter(follower = user, following = following).delete()
            following.followersC -=1
            following.save()
            user.followingC -= 1
            user.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'following': False, 'followers': following.followersC})
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
                    body=_("%(name)s começou a te seguir") % {"name": user.name},
                    linkzaocarai=f"{user.username}/",
                )
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'following': True, 'followers': following.followersC})
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
                messages.error(request, _('Você não pode deletar esta resposta.'))
                return redirect(next_url)
            for child in Replys.objects.filter(tweet=reply.tweet, reply=reply):
                child.reply.remove(reply)
            reply.delete()
            messages.success(request, _('Resposta deletada.'))
            return redirect(next_url)

        tweet = get_object_or_404(Tweet, id=request.POST.get('tweetid'))
        if tweet.tweetAuthor_id != request.user.id:
            messages.error(request, _('Você não pode deletar este tweet.'))
            return redirect(next_url)
        tweet.delete()
        messages.success(request, _('Tweet deletado.'))
        return redirect(next_url)

@login_required(login_url='/login')
def report(request):
    if request.method == 'POST':
        kind, target = post_target(request)
        author_id = target.user_id if kind == 'reply' else target.tweetAuthor_id
        if author_id == request.user.id:
            return HttpResponseForbidden(_('Você não pode denunciar sua própria publicação.'))
        reason = request.POST.get('reason', '').strip()
        if reason and len(reason) <= 100:
            Report.objects.create(x9=request.user, reason=reason, **{kind: target})
            messages.success(request, _('Denuncia registrada.'))
        else:
            messages.error(request, _('Informe um motivo de até 100 caracteres.'))
        return redirect(request.POST.get('next', '/'))
    return redirect('/')
