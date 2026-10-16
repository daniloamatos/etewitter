import io
import tempfile
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image

from main.image_utils import (
    validate_banner_image_size,
    validate_image_size,
    validate_profile_image_size,
)
from main.models import Follower, ReplyRetweet, Replys, SavedItems, Tweet, TweetRetweet
from register.models import Usuario


class CoreFlowTests(TestCase):
    def setUp(self):
        self.user = Usuario.objects.create_user(
            username='tester',
            email='tester@example.com',
            password='Test@123456',
            name='Tester',
            usernameinsensitive='TESTER',
            is_active=True,
        )
        self.other = Usuario.objects.create_user(
            username='other',
            email='other@example.com',
            password='Other@123456',
            name='Other',
            usernameinsensitive='OTHER',
            is_active=True,
        )
        self.third = Usuario.objects.create_user(
            username='third',
            email='third@example.com',
            password='Third@123456',
            name='Third',
            usernameinsensitive='THIRD',
            is_active=True,
        )

    def test_notifications_are_ordered_by_occurrence_time(self):
        from main.models import Notification

        now = timezone.now()
        older = Notification.objects.create(
            user=self.user, actor=self.other, body='Aviso antigo',
            linkzaocarai='other/', publishDate=now - timedelta(days=1),
        )
        newer = Notification.objects.create(
            user=self.user, actor=self.third, body='Aviso novo',
            linkzaocarai='third/', publishDate=now,
        )
        self.client.force_login(self.user)
        response = self.client.get('/notifications/')
        html = response.content.decode()
        self.assertLess(html.index(f'data-notification-id="{newer.pk}"'),
                        html.index(f'data-notification-id="{older.pk}"'))

    def test_mention_suggestions_only_include_followed_matching_accounts(self):
        Follower.objects.create(follower=self.user, following=self.other)
        self.client.force_login(self.user)

        self.assertEqual(
            [user['username'] for user in self.client.get('/mention-suggestions/', {'q': '@oth'}).json()['users']],
            ['other'],
        )
        self.assertEqual(
            [user['username'] for user in self.client.get('/mention-suggestions/', {'q': ''}).json()['users']],
            ['other'],
        )
        self.assertEqual(self.client.get('/mention-suggestions/', {'q': 'third'}).json()['users'], [])
        self.assertContains(self.client.get('/search/', {'query': '@other'}), '/other/')

    def test_mentions_multiple_handles_and_safe_rendering(self):
        from main.models import Notification
        from main.templatetags.custom_filters import render_mentions
        self.client.force_login(self.user)
        body = '<script>alert(1)</script> @OTHER, @other! @third @tester @missinguser email@other @other_invalid'
        self.client.post('/', {'tweet': body})
        post = Tweet.objects.get(tweetAuthor=self.user)
        self.assertEqual(set(post.mentions.all()), {self.user, self.other, self.third})
        self.assertEqual(Notification.objects.filter(notification_type='mention').count(), 2)
        rendered = render_mentions(body)
        self.assertIn('&lt;script&gt;', rendered)
        self.assertNotIn('<script>', rendered)
        self.assertEqual(rendered.count('href="/other/"'), 2)
        self.assertIn('email@other @other_invalid', rendered)
        response = self.client.get('/' + post.tweetLink)
        self.assertContains(response, 'class="profile-handle-link mention-link"')
        self.assertNotContains(response, '<a class="tweet-content')

    def test_mentioned_users_receive_post_interactions(self):
        from main.models import Notification
        self.client.force_login(self.user)
        self.client.post('/', {'tweet': 'Hello @other @tester'})
        post = Tweet.objects.get(tweetAuthor=self.user)
        Notification.objects.all().delete()
        self.client.force_login(self.third)
        for endpoint, kind in [('like', 'like'), ('retweet', 'retweet')]:
            self.client.post('/tester/' + endpoint + '/', {'tweetid': str(post.pk)})
            self.assertEqual(set(Notification.objects.filter(notification_type=kind).values_list('user_id', flat=True)), {self.user.pk, self.other.pk})
            self.client.post('/tester/' + endpoint + '/', {'tweetid': str(post.pk)})
            self.assertEqual(Notification.objects.filter(notification_type=kind).count(), 2)
        self.client.post('/third/status/reply', {'tweetid': str(post.pk), 'body': 'Reply @other'})
        child = Replys.objects.get(tweet=post)
        self.assertEqual(Notification.objects.filter(reply=child, user=self.other).count(), 1)
        self.assertEqual(Notification.objects.get(reply=child, user=self.other).notification_type, 'mention')
        self.client.force_login(self.other)
        response = self.client.get('/notifications/')
        self.assertContains(response, 'curtiu uma publicação em que você foi mencionado')

    def test_nested_mentions_and_profile_composer(self):
        from main.models import Notification
        self.client.force_login(self.user)
        self.client.post('/tester/', {'tweet': 'Profile @other'})
        root = Tweet.objects.get(tweetAuthor=self.user)
        self.assertTrue(root.mentions.filter(pk=self.other.pk).exists())
        self.client.post('/tester/status/reply', {'tweetid': str(root.pk), 'body': 'First'})
        parent = Replys.objects.get(tweet=root)
        self.client.post('/tester/status/reply', {'tweetid': str(parent.pk), 'content_type': 'reply', 'body': 'Child @third!'})
        child = Replys.objects.exclude(pk=parent.pk).get()
        self.assertTrue(child.mentions.filter(pk=self.third.pk).exists())
        self.assertEqual(Notification.objects.filter(user=self.third, reply=child, notification_type='mention').count(), 1)
        self.client.force_login(self.other)
        self.client.post('/likereply/', {'replyid': str(child.pk)})
        self.client.post('/other/retweet-reply/', {'replyid': str(child.pk)})
        for kind in ['like', 'retweet']:
            self.assertTrue(Notification.objects.filter(user=self.third, reply=child, notification_type=kind).exists())
        self.client.post('/other/status/reply', {'tweetid': str(child.pk), 'content_type': 'reply', 'body': 'Grandchild'})
        grandchild = Replys.objects.get(body='Grandchild')
        self.assertTrue(Notification.objects.filter(user=self.third, reply=grandchild, notification_type='reply').exists())
        self.assertFalse(Notification.objects.filter(user=self.other, actor=self.other).exists())

    def test_profile_preview_and_follows_you(self):
        self.other.bio = 'Sobre esta pessoa'
        self.other.save(update_fields=['bio'])
        Follower.objects.create(follower=self.other, following=self.user)
        self.client.force_login(self.user)

        response = self.client.get('/profile-preview/other/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['bio'], 'Sobre esta pessoa')
        self.assertTrue(response.json()['follows_you'])
        self.assertFalse(response.json()['is_following'])
        badge = '<p class="profile-follows-you">Segue você</p>'
        self.assertContains(self.client.get('/other/'), badge)
        self.assertNotContains(self.client.get('/third/'), badge)

        response = self.client.post('/follow/', {'userP': str(self.other.pk)},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.json()['following'], True)
        self.assertEqual(response.json()['followers'], 1)
        self.assertTrue(self.client.get('/profile-preview/other/').json()['is_following'])

        response = self.client.post('/follow/', {'userP': str(self.other.pk)},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.json()['following'], False)
        self.assertEqual(response.json()['followers'], 0)

    def test_login_accepts_username_case_insensitively(self):
        response = self.client.post(
            '/login/',
            {'usuario': 'TESTER', 'senha': 'Test@123456'},
        )
        self.assertRedirects(response, '/')

    def test_tweet_creation_with_mention_does_not_require_existing_user(self):
        self.client.force_login(self.user)
        response = self.client.post('/', {'tweet': 'Olá @missinguser'})
        self.assertRedirects(response, '/')
        self.assertEqual(Tweet.objects.filter(tweetAuthor=self.user).count(), 1)

    def test_user_cannot_delete_another_users_tweet(self):
        tweet = Tweet.objects.create(tweetAuthor=self.other, tweet='Protegido')
        self.client.force_login(self.user)
        response = self.client.post('/delete/', {'tweetid': tweet.pk})
        self.assertRedirects(response, '/')
        self.assertTrue(Tweet.objects.filter(pk=tweet.pk).exists())

    def test_user_can_delete_own_tweet_from_requested_page(self):
        tweet = Tweet.objects.create(tweetAuthor=self.user, tweet='Excluir da inicial')
        self.client.force_login(self.user)
        response = self.client.post('/delete/', {
            'tweetid': tweet.pk,
            'next': '/',
        })
        self.assertRedirects(response, '/')
        self.assertFalse(Tweet.objects.filter(pk=tweet.pk).exists())

    def test_user_can_delete_own_reply_without_deleting_parent_tweet(self):
        tweet = Tweet.objects.create(tweetAuthor=self.other, tweet='Pai')
        reply = Replys.objects.create(
            user=self.user,
            tweet=tweet,
            body='Filho',
            replyLink='tester/status/filho',
        )
        self.client.force_login(self.user)
        response = self.client.post('/delete/', {
            'content_type': 'reply',
            'tweetid': reply.pk,
            'next': '/other/status/pai',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/other/status/pai')
        self.assertFalse(Replys.objects.filter(pk=reply.pk).exists())
        self.assertTrue(Tweet.objects.filter(pk=tweet.pk).exists())

    def test_saving_a_tweet_is_scoped_to_current_user(self):
        tweet = Tweet.objects.create(tweetAuthor=self.other, tweet='Salvável')
        SavedItems.objects.create(user=self.other, tweet=tweet)
        self.client.force_login(self.user)

        response = self.client.post('/save/', {
            'tweetid': tweet.pk,
            'next': '/',
        })

        self.assertEqual(response.status_code, 204)
        self.assertTrue(
            SavedItems.objects.filter(user=self.user, tweet=tweet).exists()
        )

    def test_liking_a_tweet_toggles_without_redirect(self):
        tweet = Tweet.objects.create(tweetAuthor=self.other, tweet='Curtível')
        self.client.force_login(self.user)

        response = self.client.post('/like/', {
            'tweetid': tweet.pk,
            'next': '/demo1234/',
        })

        self.assertEqual(response.status_code, 204)
        tweet.refresh_from_db()
        self.assertEqual(tweet.likec, 1)
        self.assertTrue(tweet.likes.filter(pk=self.user.pk).exists())

        response = self.client.post('/like/', {
            'tweetid': tweet.pk,
            'next': '/demo1234/',
        })

        self.assertEqual(response.status_code, 204)
        tweet.refresh_from_db()
        self.assertEqual(tweet.likec, 0)
        self.assertFalse(tweet.likes.filter(pk=self.user.pk).exists())

    def test_retweeting_tweets_and_replies_toggles(self):
        tweet = Tweet.objects.create(tweetAuthor=self.other, tweet='Retweetável')
        reply = Replys.objects.create(
            user=self.other,
            tweet=tweet,
            body='Resposta retweetável',
            replyLink='other/status/reply',
        )
        self.client.force_login(self.user)

        response = self.client.post('/tester/retweet/', {
            'tweetid': tweet.pk,
            'next': '/',
        })
        self.assertEqual(response.status_code, 204)
        self.assertTrue(tweet.retweets.filter(pk=self.user.pk).exists())

        response = self.client.post('/tester/retweet-reply/', {
            'replyid': reply.pk,
            'next': '/',
        })
        self.assertEqual(response.status_code, 204)
        self.assertTrue(reply.retweets.filter(pk=self.user.pk).exists())

    def test_tweet_retweet_uses_retweet_time_in_home_timeline(self):
        old = Tweet.objects.create(tweetAuthor=self.third, tweet='Post antigo')
        recent = Tweet.objects.create(tweetAuthor=self.other, tweet='Post recente')
        now = timezone.now()
        Tweet.objects.filter(pk=old.pk).update(publishDate=now - timedelta(days=3))
        Tweet.objects.filter(pk=recent.pk).update(publishDate=now - timedelta(hours=1))
        Follower.objects.create(follower=self.user, following=self.other)
        self.client.force_login(self.other)
        self.client.post('/other/retweet/', {'tweetid': old.pk})
        event = TweetRetweet.objects.get(tweet=old, user=self.other)
        self.assertGreater(event.created_at, recent.publishDate)

        self.client.force_login(self.user)
        timeline = self.client.get('/').context['timeline']
        self.assertEqual([item.pk for item in timeline[:2]], [old.pk, recent.pk])
        self.assertEqual(timeline[0].retweet_by_username, 'other')
        self.assertEqual(timeline[0].timeline_date, event.created_at)
        self.assertEqual(timeline[0].publishDate.date(), (now - timedelta(days=3)).date())

    def test_reply_retweet_uses_retweet_time_in_profile_timeline(self):
        root = Tweet.objects.create(tweetAuthor=self.third, tweet='Raiz')
        reply = Replys.objects.create(user=self.third, tweet=root, body='Resposta antiga')
        recent = Tweet.objects.create(tweetAuthor=self.other, tweet='Post recente')
        now = timezone.now()
        Replys.objects.filter(pk=reply.pk).update(publishDate=now - timedelta(days=3))
        Tweet.objects.filter(pk=recent.pk).update(publishDate=now - timedelta(hours=1))
        self.client.force_login(self.other)
        self.client.post('/other/retweet-reply/', {'replyid': reply.pk})
        event = ReplyRetweet.objects.get(reply=reply, user=self.other)

        timeline = self.client.get('/other/').context['timeline']
        self.assertEqual([item.pk for item in timeline[:2]], [reply.pk, recent.pk])
        self.assertEqual(timeline[0].timeline_date, event.created_at)

    def test_each_retweet_is_a_separate_event_and_reposting_gets_new_time(self):
        tweet = Tweet.objects.create(tweetAuthor=self.user, tweet='Compartilhado')
        tweet.retweets.add(self.other, self.third)
        old_time = timezone.now() - timedelta(days=2)
        TweetRetweet.objects.filter(tweet=tweet, user=self.other).update(created_at=old_time)
        Follower.objects.create(follower=self.user, following=self.other)
        Follower.objects.create(follower=self.user, following=self.third)
        self.client.force_login(self.user)
        timeline = self.client.get('/').context['timeline']
        retweets = [item for item in timeline if getattr(item, 'retweet_by_username', None)]
        self.assertEqual([item.retweet_by_username for item in retweets], ['third', 'other'])

        self.client.force_login(self.other)
        self.client.post('/other/retweet/', {'tweetid': tweet.pk})
        self.assertFalse(TweetRetweet.objects.filter(tweet=tweet, user=self.other).exists())
        self.client.post('/other/retweet/', {'tweetid': tweet.pk})
        self.assertGreater(TweetRetweet.objects.get(tweet=tweet, user=self.other).created_at, old_time)

    def test_retweeted_tweet_appears_on_retweeter_profile(self):
        tweet = Tweet.objects.create(
            tweetAuthor=self.third,
            tweet='Original que foi retweetado',
            tweetLink='third/status/original',
        )
        tweet.retweets.add(self.other)
        self.client.force_login(self.user)

        response = self.client.get('/other/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Original que foi retweetado')
        self.assertContains(response, 'href="/other/">@other</a> repostou')

    def test_retweeted_tweet_appears_in_followers_feed(self):
        tweet = Tweet.objects.create(
            tweetAuthor=self.third,
            tweet='Tweet distribuído pelo retweet',
            tweetLink='third/status/distributed',
        )
        tweet.retweets.add(self.other)
        Follower.objects.create(follower=self.user, following=self.other)
        self.client.force_login(self.user)

        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tweet distribuído pelo retweet')
        self.assertContains(response, 'href="/other/">@other</a> repostou')

    def test_reply_like_toggles_without_redirect(self):
        tweet = Tweet.objects.create(tweetAuthor=self.other, tweet='Pai')
        reply = Replys.objects.create(
            user=self.other,
            tweet=tweet,
            body='Resposta',
            replyLink='other/status/reply',
        )
        self.client.force_login(self.user)
        response = self.client.post('/likereply/', {
            'replyid': reply.pk,
            'next': '/',
        })
        self.assertEqual(response.status_code, 204)
        reply.refresh_from_db()
        self.assertEqual(reply.likec, 1)
        self.assertTrue(reply.likes.filter(pk=self.user.pk).exists())

    def test_reply_detail_contains_only_its_parent_chain(self):
        root = Tweet.objects.create(tweetAuthor=self.other, tweet='Tweet raiz')
        unrelated = Tweet.objects.create(tweetAuthor=self.other, tweet='Tweet sem relação')
        parent = Replys.objects.create(
            user=self.other,
            tweet=root,
            body='Resposta pai',
            replyLink='other/status/parent',
        )
        current = Replys.objects.create(
            user=self.user,
            tweet=root,
            body='Resposta atual',
            replyLink='other/status/current',
        )
        current.reply.add(parent)
        Replys.objects.create(
            user=self.other,
            tweet=unrelated,
            body='Resposta de outro tweet',
            replyLink='other/status/unrelated',
        )
        self.client.force_login(self.user)

        response = self.client.get('/other/status/current')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tweet raiz')
        self.assertContains(response, 'Resposta pai')
        self.assertContains(response, 'Resposta atual')
        content = response.content.decode()
        self.assertLess(content.index('Tweet raiz'), content.index('Resposta pai'))
        self.assertLess(content.index('Resposta pai'), content.index('Resposta atual'))
        self.assertContains(response, f'href="/{root.tweetLink}"')
        self.assertContains(response, 'href="/other/status/parent"')
        self.assertNotContains(response, 'Tweet sem relação')
        self.assertNotContains(response, 'Resposta de outro tweet')

    def test_parent_detail_shows_reply_avatar_and_delete_modal_for_reply_owner(self):
        self.user.profilepic.save(
            'reply-avatar.png',
            SimpleUploadedFile(
                'reply-avatar.png',
                b'avatar-data',
                content_type='image/png',
            ),
        )
        self.user.save()
        root = Tweet.objects.create(
            tweetAuthor=self.other,
            tweet='Tweet pai',
            tweetLink='other/status/parent-with-reply',
        )
        reply = Replys.objects.create(
            user=self.user,
            tweet=root,
            body='Meu filho',
            replyLink='tester/status/my-child',
        )
        self.client.force_login(self.user)

        response = self.client.get(f'/{root.tweetLink}')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'src="{self.user.profilepic.url}"')
        self.assertContains(response, f'data-delete-id="{reply.id}" data-delete-kind="reply"')
        self.assertContains(response, 'id="post-delete-dialog"')

        response = self.client.post('/delete/', {
            'content_type': 'reply',
            'tweetid': reply.pk,
            'next': f'/{root.tweetLink}',
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], f'/{root.tweetLink}')
        self.assertFalse(Replys.objects.filter(pk=reply.pk).exists())

    def test_reply_chain_does_not_repeat_parent_as_child(self):
        root = Tweet.objects.create(
            tweetAuthor=self.other,
            tweet='1',
            tweetLink='other/status/root',
        )
        parent = Replys.objects.create(
            user=self.other,
            tweet=root,
            body='2',
            replyLink='other/status/2',
        )
        current = Replys.objects.create(
            user=self.user,
            tweet=root,
            body='4',
            replyLink='other/status/4',
        )
        current.reply.add(parent)
        self.client.force_login(self.user)

        response = self.client.get('/other/status/4')

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertEqual(content.count('>2<'), 1)
        self.assertEqual(content.count('>4<'), 1)

    def test_nested_reply_shows_link_to_its_deeper_responses(self):
        root = Tweet.objects.create(
            tweetAuthor=self.other,
            tweet='raiz',
            tweetLink='other/status/root',
        )
        parent = Replys.objects.create(
            user=self.other,
            tweet=root,
            body='pai',
            replyLink='other/status/pai',
        )
        current = Replys.objects.create(
            user=self.user,
            tweet=root,
            body='neto',
            replyLink='other/status/neto',
        )
        child = Replys.objects.create(
            user=self.other,
            tweet=root,
            body='bisneto',
            replyLink='other/status/bisneto',
        )
        current.reply.add(parent)
        child.reply.add(current)
        self.client.force_login(self.user)

        response = self.client.get('/other/status/pai')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'neto')
        self.assertContains(response, 'Ver mais respostas')
        self.assertContains(response, '/other/status/neto')

    def test_search_matches_tweets_and_replies_case_insensitively_by_partial_text(self):
        tweet = Tweet.objects.create(
            tweetAuthor=self.other,
            tweet='Um texto interessante sobre Django',
            tweetLink='other/status/search-tweet',
        )
        reply = Replys.objects.create(
            user=self.user,
            tweet=tweet,
            body='Comentário interessante também',
            replyLink='tester/status/search-reply',
        )

        response = self.client.get('/search/', {'query': 'INTERESS'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, tweet.tweet)
        self.assertContains(response, reply.body)
        self.assertContains(response, reply.replyLink)
        self.assertContains(response, 'Resposta')
        self.assertContains(response, 'Em resposta a')
        self.assertContains(response, tweet.tweet)

        response = self.client.get('/search/', {'query': 'INTERESS'})
        self.assertEqual(response.status_code, 200)

    def test_root_detail_shows_direct_replies_and_link_to_deeper_branch(self):
        root = Tweet.objects.create(
            tweetAuthor=self.other,
            tweet='1',
            tweetLink='other/status/root',
        )
        first = Replys.objects.create(
            user=self.other, tweet=root, body='2', replyLink='other/status/2'
        )
        second = Replys.objects.create(
            user=self.user, tweet=root, body='3', replyLink='other/status/3'
        )
        fourth = Replys.objects.create(
            user=self.user, tweet=root, body='4', replyLink='other/status/4'
        )
        fifth = Replys.objects.create(
            user=self.other, tweet=root, body='5', replyLink='other/status/5'
        )
        fourth.reply.add(first)
        fifth.reply.add(second)
        self.client.force_login(self.user)

        response = self.client.get('/other/status/root')

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertEqual(content.count('>2<'), 1)
        self.assertEqual(content.count('>3<'), 1)
        self.assertNotIn('>4<', content)
        self.assertNotIn('>5<', content)
        self.assertContains(response, 'Ver mais respostas', count=2)

    def test_clearing_profile_photos_removes_uploaded_files_without_invalid_default_paths(self):
        self.user.profilepic.save(
            'avatar.png',
            SimpleUploadedFile('avatar.png', b'avatar-data', content_type='image/png'),
        )
        self.user.bannerpic.save(
            'banner.png',
            SimpleUploadedFile('banner.png', b'banner-data', content_type='image/png'),
        )
        self.user.save()
        self.client.force_login(self.user)

        response = self.client.post('/editprofile/', {
            'name': self.user.name,
            'bio': 'Bio atualizada',
            'profilepic-clear': 'on',
            'bannerpic-clear': 'on',
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/editprofile')
        self.user.refresh_from_db()
        self.assertEqual(self.user.profilepic.name, '')
        self.assertEqual(self.user.bannerpic.name, '')
        self.assertFalse(self.user.profilepic.storage.exists('avatar.png'))
        self.assertFalse(self.user.bannerpic.storage.exists('banner.png'))

    def test_tweet_detail_uses_author_profile_photo_for_root_tweet(self):
        self.user.profilepic.save(
            'detail-avatar.png',
            SimpleUploadedFile(
                'detail-avatar.png',
                b'avatar-data',
                content_type='image/png',
            ),
        )
        self.user.save()
        tweet = Tweet.objects.create(
            tweetAuthor=self.user,
            tweet='Tweet com avatar',
            tweetLink='tester/status/detail-avatar',
        )
        self.client.force_login(self.other)

        response = self.client.get(f'/{tweet.tweetLink}')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'src="{self.user.profilepic.url}"')
        self.assertNotContains(response, '>T</div>')

    def test_home_delete_modal_uses_the_rendered_modal_id(self):
        tweet = Tweet.objects.create(
            tweetAuthor=self.user,
            tweet='Tweet com exclusão',
            tweetLink='tester/status/delete-modal',
        )
        self.client.force_login(self.user)

        response = self.client.get('/')

        self.assertContains(
            response,
            f'data-delete-id="{tweet.id}" data-delete-kind="tweet"',
        )
        self.assertContains(response, 'id="post-delete-dialog"')

    def test_saved_tweets_are_private_idempotent_and_deleted_with_original(self):
        tweet = Tweet.objects.create(
            tweetAuthor=self.other, tweet='Salvo privado',
            tweetLink='other/status/private-save',
        )
        self.client.force_login(self.user)
        for _ in range(2):
            self.client.post('/save/', {'tweetid': tweet.pk, 'action': 'save'})
        self.assertEqual(SavedItems.objects.filter(user=self.user, tweet=tweet).count(), 1)
        self.assertContains(self.client.get('/saveditems/'), tweet.tweet)
        self.client.force_login(self.third)
        self.assertNotContains(self.client.get('/saveditems/'), tweet.tweet)
        self.client.post('/save/', {'tweetid': tweet.pk, 'action': 'save'})
        self.client.post('/save/', {'tweetid': tweet.pk, 'action': 'remove'})
        self.assertTrue(SavedItems.objects.filter(user=self.user, tweet=tweet).exists())
        self.assertFalse(SavedItems.objects.filter(user=self.third, tweet=tweet).exists())
        self.client.force_login(self.other)
        self.client.post('/delete/', {'tweetid': tweet.pk})
        self.assertFalse(SavedItems.objects.filter(tweet_id=tweet.pk).exists())
        self.client.force_login(self.user)
        self.assertNotContains(self.client.get('/saveditems/'), 'Salvo privado')

    def test_retweeted_reply_is_visible_in_profile_own_feed_and_followers_feed(self):
        root = Tweet.objects.create(tweetAuthor=self.third, tweet='Raiz')
        reply = Replys.objects.create(
            user=self.third, tweet=root, body='Resposta compartilhada',
            replyLink='third/status/shared-child',
        )
        self.client.force_login(self.other)
        self.client.post('/other/retweet-reply/', {'replyid': reply.pk})
        for url in ('/', '/other/'):
            response = self.client.get(url)
            self.assertContains(response, reply.body)
            self.assertContains(response, 'href="/other/">@other</a> repostou')
            self.assertContains(response, f'href="/{reply.replyLink}"')
            self.assertNotContains(response, 'Seu feed está vazio')
            self.assertNotContains(response, 'Nenhum tweet ainda')
        Follower.objects.create(follower=self.user, following=self.other)
        self.client.force_login(self.user)
        self.assertContains(self.client.get('/'), reply.body)
        self.client.force_login(self.other)
        self.client.post('/other/retweet-reply/', {'replyid': reply.pk})
        self.assertNotContains(self.client.get('/other/'), reply.body)
        self.assertNotContains(self.client.get('/'), reply.body)
        self.client.force_login(self.user)
        self.assertNotContains(self.client.get('/'), reply.body)

    def test_thread_reply_uses_shared_card_and_heart_icon(self):
        root = Tweet.objects.create(
            tweetAuthor=self.other, tweet='Raiz', tweetLink='other/status/layout',
        )
        Replys.objects.create(user=self.user, tweet=root, body='Filho', replyLink='tester/status/layout-child')
        self.client.force_login(self.user)
        response = self.client.get('/other/status/layout')
        self.assertTemplateUsed(response, 'main/reply_card.html')
        self.assertContains(response, 'tweet-card reply-tweet-card')
        self.assertNotContains(response, 'reply-card-avatar-link')
        self.assertNotContains(response, 'A4.8 4.8 0 0 0 12 6')
        self.assertContains(response, 'action="/save/"')

    def test_child_save_and_report_target_the_child_not_the_root(self):
        from main.models import Report
        root = Tweet.objects.create(tweetAuthor=self.other, tweet='Raiz exclusiva', tweetLink='other/status/root-unico')
        child = Replys.objects.create(tweet=root, user=self.third, body='Filho exclusivo', replyLink='third/status/child-unico')
        self.client.force_login(self.user)
        data = {'content_type': 'reply', 'tweetid': child.pk, 'action': 'save'}
        self.client.post('/save/', data)
        self.client.post('/save/', data)
        self.assertEqual(SavedItems.objects.filter(user=self.user, reply=child, tweet=None).count(), 1)
        self.assertFalse(SavedItems.objects.filter(user=self.user, tweet=root).exists())
        response = self.client.get('/saveditems/')
        self.assertContains(response, child.body)
        self.assertNotContains(response, root.tweet)
        self.assertContains(response, 'Remover dos salvos')
        self.client.post('/report/', {**data, 'reason': 'Conteúdo inadequado'})
        self.assertTrue(Report.objects.filter(reply=child, tweet=None, x9=self.user).exists())
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get('/saveditems/'), child.body)
        self.client.post('/save/', data)
        self.client.post('/save/', {**data, 'action': 'remove'})
        self.assertTrue(SavedItems.objects.filter(user=self.user, reply=child).exists())
        self.client.force_login(self.third)
        self.client.post('/delete/', {'content_type': 'reply', 'tweetid': child.pk})
        self.assertFalse(SavedItems.objects.filter(reply=child).exists())
        self.assertTrue(Tweet.objects.filter(pk=root.pk).exists())

    def test_saved_child_is_deleted_when_root_is_deleted(self):
        root = Tweet.objects.create(tweetAuthor=self.other, tweet='Raiz')
        child = Replys.objects.create(tweet=root, user=self.third, body='Filho')
        SavedItems.objects.create(user=self.user, reply=child)
        root.delete()
        self.assertFalse(SavedItems.objects.filter(user=self.user).exists())

    def test_post_actions_and_profile_links_are_consistent_across_pages(self):
        root = Tweet.objects.create(tweetAuthor=self.other, tweet='Publicação raiz', tweetLink='other/status/root-actions')
        child = Replys.objects.create(tweet=root, user=self.third, body='Publicação filha', replyLink='third/status/child-actions')
        root.retweets.add(self.user)
        child.retweets.add(self.user)
        SavedItems.objects.create(user=self.user, tweet=root)
        SavedItems.objects.create(user=self.user, reply=child)
        self.client.force_login(self.user)
        for url in ('/', '/tester/', '/saveditems/', '/search/?query=Publicação', '/other/status/root-actions', '/third/status/child-actions'):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, f'data-card-url="/{root.tweetLink}"')
                self.assertContains(response, f'data-card-url="/{child.replyLink}"')
                self.assertContains(response, 'href="/other/"')
                self.assertContains(response, 'href="/third/"')
                self.assertContains(response, 'name="content_type" value="reply"')
                self.assertContains(response, f'data-report-id="{child.pk}" data-report-kind="reply"')
                self.assertTemplateUsed(response, 'main/post_actions.html')

    def test_notification_actor_has_profile_links(self):
        from main.models import Notification
        Notification.objects.create(user=self.user, actor=self.other, body='other te mencionou em um tweet', linkzaocarai='other/status/mention')
        self.client.force_login(self.user)
        response = self.client.get('/notifications/')
        self.assertContains(response, 'href="/other/"')
        self.assertContains(response, 'alt="Foto de Other"')
        self.assertContains(response, 'data-card-url="/other/status/mention"')

    def test_mention_notifications_show_actor_date_and_content_without_extra_label(self):
        from main.models import Notification
        root = Tweet.objects.create(
            tweetAuthor=self.other, tweet='Post com @tester',
            tweetLink='other/status/mention-post',
        )
        reply = Replys.objects.create(
            user=self.other, tweet=root, body='Resposta com @tester',
            replyLink='other/status/mention-reply',
        )
        self.client.force_login(self.user)
        for post, text in ((root, root.tweet), (reply, reply.body)):
            notice = Notification.objects.create(
                user=self.user, actor=self.other, notification_type='mention',
                body='Other te mencionou',
                linkzaocarai=post.replyLink if isinstance(post, Replys) else post.tweetLink,
                tweet=root, reply=post if isinstance(post, Replys) else None,
            )
            with self.subTest(post=post):
                html = self.client.get(f'/notifications/{notice.pk}/').content.decode()
                self.assertIn(text.split(' @')[0], html)
                self.assertIn('@other</a><span class="notification-date-separator"', html)
                self.assertEqual(html.count('<time '), 1)
                self.assertNotIn('notification-icon', html)
                self.assertNotIn('notification-reply-context', html)
                self.assertNotIn('notification-text', html)
                self.assertNotIn('te mencionou', html)

    def test_notification_post_content_and_actions_use_site_order(self):
        from main.models import Notification
        root = Tweet.objects.create(tweetAuthor=self.user, tweet='Texto do tweet', tweetLink='tester/status/notification-root')
        reply = Replys.objects.create(user=self.other, tweet=root, body='Texto da resposta', replyLink='other/status/notification-reply')
        tweet_notice = Notification.objects.create(
            user=self.user, actor=self.other, notification_type='like',
            body='curtiu', linkzaocarai=root.tweetLink, tweet=root,
        )
        reply_notice = Notification.objects.create(
            user=self.user, actor=self.other, notification_type='reply',
            body='respondeu', linkzaocarai=reply.replyLink, reply=reply,
        )
        self.client.force_login(self.user)
        for notice, content, kind in (
            (tweet_notice, 'Texto do tweet', 'tweet'),
            (reply_notice, 'Texto da resposta', 'reply'),
        ):
            with self.subTest(kind=kind):
                response = self.client.get(f'/notifications/{notice.pk}/')
                self.assertEqual(response.status_code, 200)
                html = response.content.decode()
                self.assertIn(content, html)
                self.assertNotIn('notification-target"', html)
                self.assertLess(html.index('aria-label="Responder"'), html.index('aria-label="Retweetar"'))
                self.assertLess(html.index('aria-label="Retweetar"'), html.index('aria-label="Curtir"'))
                self.assertLess(html.index('aria-label="Curtir"'), html.index('aria-label="Salvar"'))
                self.assertIn(f'name="content_type" value="{kind}"', html)

        self.assertContains(self.client.get('/notifications/'), 'notification-post-text')
        self.client.force_login(self.third)
        self.assertEqual(self.client.get(f'/notifications/{tweet_notice.pk}/').status_code, 404)

    def test_like_and_retweet_notifications_show_compact_actor_and_target(self):
        from main.models import Notification
        tweet = Tweet.objects.create(
            tweetAuthor=self.user, tweet='Texto do post', tweetLink='tester/status/text-post',
        )
        reply = Replys.objects.create(
            user=self.user, tweet=tweet, body='', image='notifications/reply.jpg',
            replyLink='tester/status/photo-reply',
        )
        like_notice = Notification.objects.create(
            user=self.user, actor=self.other, notification_type='like',
            body='curtiu', linkzaocarai=tweet.tweetLink, tweet=tweet,
        )
        retweet_notice = Notification.objects.create(
            user=self.user, actor=self.third, notification_type='retweet',
            body='retweetou', linkzaocarai=reply.replyLink, reply=reply,
        )
        self.client.force_login(self.user)
        self.client.cookies['django_language'] = 'en-us'

        like_html = self.client.get(f'/notifications/{like_notice.pk}/').content.decode()
        self.assertIn('liked your post', like_html)
        self.assertIn('notification-activity-avatar', like_html)
        self.assertIn('profile-avatar-link notification-activity-avatar-link', like_html)
        self.assertIn('notification-post-text', like_html)
        self.assertIn('Texto do post', like_html)
        self.assertIn('<time datetime=', like_html)

        retweet_html = self.client.get(f'/notifications/{retweet_notice.pk}/').content.decode()
        self.assertIn('retweeted your reply', retweet_html)
        self.assertIn('notification-activity-thumbnail', retweet_html)
        self.assertIn('/uploads/notifications/reply.jpg', retweet_html)
        self.assertNotIn('notification-target-image', retweet_html)

    def test_deep_reply_notifies_ancestors_with_direct_parent_handle(self):
        from main.models import Notification
        root = Tweet.objects.create(
            tweetAuthor=self.user, tweet='Raiz', tweetLink='tester/status/root-thread',
        )
        child = Replys.objects.create(
            user=self.other, tweet=root, body='Filho', replyLink='other/status/thread-child',
        )
        grandchild = Replys.objects.create(
            user=self.third, tweet=root, body='Neto', replyLink='third/status/thread-grandchild',
        )
        grandchild.reply.add(child)
        self.client.force_login(self.other)

        response = self.client.post('/other/status/reply', {
            'tweetid': str(grandchild.pk), 'content_type': 'reply',
            'body': 'Bisneto', 'next': '/',
        })
        self.assertRedirects(response, '/')
        created = Replys.objects.get(body='Bisneto')
        notices = Notification.objects.filter(reply=created, notification_type='reply')
        self.assertEqual(set(notices.values_list('user_id', flat=True)), {self.user.pk, self.third.pk})

        self.client.force_login(self.user)
        notice = notices.get(user=self.user)
        html = self.client.get(f'/notifications/{notice.pk}/').content.decode()
        self.assertIn('Respondendo a', html)
        self.assertIn('href="/third/">@third</a>', html)
        self.assertNotIn('respondeu à sua publicação</p>', html)
        self.client.cookies['django_language'] = 'en-us'
        self.assertIn('Replying to', self.client.get(f'/notifications/{notice.pk}/').content.decode())

    def test_reply_and_follow_notifications_show_date_without_icons(self):
        from main.models import Notification
        root = Tweet.objects.create(tweetAuthor=self.user, tweet='Post raiz')
        reply = Replys.objects.create(user=self.other, tweet=root, body='Resposta')
        notices = [
            Notification.objects.create(
                user=self.user, actor=self.other, notification_type='reply',
                body='respondeu', linkzaocarai='other/status/reply', reply=reply,
            ),
            Notification.objects.create(
                user=self.user, actor=self.other, notification_type='follow',
                body='seguiu', linkzaocarai='other/',
            ),
        ]
        self.client.force_login(self.user)
        for notice in notices:
            with self.subTest(type=notice.notification_type):
                html = self.client.get(f'/notifications/{notice.pk}/').content.decode()
                self.assertNotIn('class="notification-icon', html)
                self.assertIn('notification-date-separator', html)
                self.assertIn('<time', html)

    def test_invalid_report_target_is_not_silently_treated_as_tweet(self):
        from main.models import Report
        root = Tweet.objects.create(tweetAuthor=self.other, tweet='Raiz')
        self.client.force_login(self.user)
        response = self.client.post('/report/', {'tweetid': root.pk, 'content_type': 'unknown', 'reason': 'Motivo'})
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Report.objects.exists())

    def test_own_posts_cannot_be_reported_including_children(self):
        from main.models import Report
        root = Tweet.objects.create(tweetAuthor=self.user, tweet='Meu tweet', tweetLink='tester/status/own-report')
        child = Replys.objects.create(user=self.user, tweet=root, body='Minha resposta', replyLink='tester/status/own-child-report')
        self.client.force_login(self.user)
        for kind, post, url in [('tweet', root, root.tweetLink), ('reply', child, child.replyLink)]:
            with self.subTest(kind=kind):
                response = self.client.get('/' + url)
                self.assertNotContains(response, f'data-report-id="{post.pk}" data-report-kind="{kind}"')
                self.assertContains(response, f'data-delete-id="{post.pk}" data-delete-kind="{kind}"')
                response = self.client.post('/report/', {'tweetid': post.pk, 'content_type': kind, 'reason': 'Motivo'})
                self.assertEqual(response.status_code, 403)
        self.assertFalse(Report.objects.exists())
        self.client.force_login(self.other)
        for kind, post, url in [('tweet', root, root.tweetLink), ('reply', child, child.replyLink)]:
            with self.subTest(other_user_kind=kind):
                response = self.client.get('/' + url)
                self.assertContains(response, f'data-report-id="{post.pk}" data-report-kind="{kind}"')
                response = self.client.post('/report/', {'tweetid': post.pk, 'content_type': kind, 'reason': 'Motivo'})
                self.assertEqual(response.status_code, 302)
        self.assertEqual(Report.objects.count(), 2)


def _image_bytes(width, height, fmt='PNG'):
    buffer = io.BytesIO()
    Image.new('RGB', (width, height), (30, 140, 90)).save(buffer, format=fmt)
    return buffer.getvalue()


class _SizedFile:
    def __init__(self, size):
        self.size = size


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ImageUploadTests(TestCase):
    def setUp(self):
        self.user = Usuario.objects.create_user(
            username='imageuser',
            email='image@example.com',
            password='Test@123456',
            name='Image User',
            usernameinsensitive='IMAGEUSER',
            is_active=True,
        )

    def test_size_validators_enforce_each_limit(self):
        validate_image_size(_SizedFile(5 * 1024 * 1024))
        with self.assertRaises(ValidationError):
            validate_image_size(_SizedFile(5 * 1024 * 1024 + 1))

        validate_profile_image_size(_SizedFile(20 * 1024 * 1024))
        with self.assertRaises(ValidationError):
            validate_profile_image_size(_SizedFile(20 * 1024 * 1024 + 1))

        validate_banner_image_size(_SizedFile(50 * 1024 * 1024))
        with self.assertRaises(ValidationError):
            validate_banner_image_size(_SizedFile(50 * 1024 * 1024 + 1))

    def test_tweet_image_is_compressed_to_jpeg_and_resized(self):
        tweet = Tweet.objects.create(
            tweetAuthor=self.user,
            tweet='Com imagem',
            image=SimpleUploadedFile('wide.png', _image_bytes(3000, 2000), content_type='image/png'),
        )
        tweet.refresh_from_db()
        self.assertTrue(tweet.image.name.endswith('.jpg'))
        with Image.open(tweet.image.path) as saved:
            self.assertEqual(saved.format, 'JPEG')
            self.assertLessEqual(max(saved.size), 1600)

    def test_profile_and_banner_images_are_compressed(self):
        self.user.profilepic = SimpleUploadedFile('p.png', _image_bytes(3000, 3000), content_type='image/png')
        self.user.bannerpic = SimpleUploadedFile('b.png', _image_bytes(4000, 1500), content_type='image/png')
        self.user.save()
        self.user.refresh_from_db()
        self.assertTrue(self.user.profilepic.name.endswith('.jpg'))
        self.assertTrue(self.user.bannerpic.name.endswith('.jpg'))
        with Image.open(self.user.profilepic.path) as profile, Image.open(self.user.bannerpic.path) as banner:
            self.assertEqual(profile.format, 'JPEG')
            self.assertEqual(banner.format, 'JPEG')
            self.assertLessEqual(max(profile.size), 1600)
            self.assertLessEqual(max(banner.size), 1600)

    def test_unsupported_format_is_rejected(self):
        from main.forms import tweetForm
        form = tweetForm(
            data={'tweet': 'oi'},
            files={'image': SimpleUploadedFile('x.bmp', _image_bytes(50, 50, 'BMP'), content_type='image/bmp')},
        )
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)
