from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from main.models import Follower, Replys, SavedItems, Tweet
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

        self.assertRedirects(response, '/')
        self.assertTrue(
            SavedItems.objects.filter(user=self.user, tweet=tweet).exists()
        )

    def test_liking_a_tweet_redirects_back_and_toggles(self):
        tweet = Tweet.objects.create(tweetAuthor=self.other, tweet='Curtível')
        self.client.force_login(self.user)

        response = self.client.post('/like/', {
            'tweetid': tweet.pk,
            'next': '/demo1234/',
        })

        self.assertRedirects(response, '/demo1234/')
        tweet.refresh_from_db()
        self.assertEqual(tweet.likec, 1)
        self.assertTrue(tweet.likes.filter(pk=self.user.pk).exists())

        response = self.client.post('/like/', {
            'tweetid': tweet.pk,
            'next': '/demo1234/',
        })

        self.assertRedirects(response, '/demo1234/')
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
        self.assertRedirects(response, '/')
        self.assertTrue(tweet.retweets.filter(pk=self.user.pk).exists())

        response = self.client.post('/tester/retweet-reply/', {
            'replyid': reply.pk,
            'next': '/',
        })
        self.assertRedirects(response, '/')
        self.assertTrue(reply.retweets.filter(pk=self.user.pk).exists())

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
        self.assertContains(response, '<a href="/other/">Other</a> retweetou')

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
        self.assertContains(response, '<a href="/other/">Other</a> retweetou')

    def test_reply_like_redirects_and_toggles(self):
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
        self.assertRedirects(response, '/')
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
            self.assertContains(response, '<a href="/other/">Other</a> retweetou')
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

    def test_child_save_and_report_target_the_child_when_ids_overlap(self):
        from main.models import Report
        root = Tweet.objects.create(id=900, tweetAuthor=self.other, tweet='Raiz exclusiva', tweetLink='other/status/root900')
        child = Replys.objects.create(id=900, tweet=root, user=self.third, body='Filho exclusivo', replyLink='third/status/child900')
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
        self.assertFalse(SavedItems.objects.filter(reply_id=900).exists())
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
