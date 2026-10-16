from django.shortcuts import render
from main.models import Replys, Tweet
from register.models import Usuario

def search(request, **query):
    query = request.GET.get('query', '').strip()
    lookup = query[1:] if query.startswith('@') else query
    if request.method == 'GET':
        result1 = Usuario.objects.filter(username__icontains=lookup)
        result2 = Tweet.objects.filter(tweet__icontains=query)
        result3 = Usuario.objects.filter(name__icontains=lookup)
        result4 = []
        for reply in Replys.objects.filter(body__icontains=query).select_related(
            'user', 'tweet', 'tweet__tweetAuthor'
        ).prefetch_related('reply'):
            parent_reply = reply.reply.order_by('-publishDate').first()
            parent = parent_reply or reply.tweet
            result4.append({
                'reply': reply,
                'parent_url': parent.replyLink if parent_reply else parent.tweetLink,
                'parent_username': parent.user.username if parent_reply else parent.tweetAuthor.username,
                'parent_text': parent.body if parent_reply else parent.tweet,
                'parent_image': parent.image,
            })
        return render(request, "main/searchresult.html", {
            'result1': result1,
            'result2': result2,
            'result3': result3,
            'result4': result4,
            'query': query,
        })
    
