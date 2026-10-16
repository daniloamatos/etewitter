from django.test import TestCase
from main.models import Message
from register.models import Usuario


class ConversationTests(TestCase):
    def test_history_does_not_render_as_flash_messages(self):
        sender = Usuario.objects.create_user(username='sender', email='sender@example.test')
        receiver = Usuario.objects.create_user(username='receiver', email='receiver@example.test')
        Message.objects.create(sender=sender, receiver=receiver, body='Mensagem no histórico')
        self.client.force_login(sender)
        response = self.client.get(f'/messages/{sender.pk}-{receiver.pk}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mensagem no histórico', count=1)
        self.assertNotContains(response, 'flash-stack')
        self.assertContains(response, 'name="message" aria-label="Mensagem"')
        self.assertContains(response, '>Enviar</button>')

    def test_unread_badge_is_private_and_opening_chat_reads_only_that_sender(self):
        sender = Usuario.objects.create_user(username='sender', email='sender@example.test')
        receiver = Usuario.objects.create_user(username='receiver', email='receiver@example.test')
        third = Usuario.objects.create_user(username='third', email='third@example.test')
        incoming = Message.objects.create(sender=sender, receiver=receiver, body='Primeira')
        other = Message.objects.create(sender=third, receiver=receiver, body='Outra conversa')
        self.client.force_login(sender)
        self.assertFalse(self.client.get('/').context['has_unread_messages'])
        self.client.force_login(receiver)
        self.assertTrue(self.client.get('/').context['has_unread_messages'])
        self.client.get(f'/messages/{receiver.pk}-{sender.pk}')
        incoming.refresh_from_db()
        other.refresh_from_db()
        self.assertTrue(incoming.is_read)
        self.assertFalse(other.is_read)
        self.assertTrue(self.client.get('/').context['has_unread_messages'])
        self.client.get(f'/messages/{receiver.pk}-{third.pk}')
        self.assertFalse(self.client.get('/').context['has_unread_messages'])

    def test_message_creates_unread_state_without_notification(self):
        from chat.consumers import ChatConsumer
        from main.models import Notification
        sender = Usuario.objects.create_user(username='sender', email='sender@example.test')
        receiver = Usuario.objects.create_user(username='receiver', email='receiver@example.test')
        message = ChatConsumer().save_message('Olá', sender, receiver)
        self.assertFalse(message.is_read)
        self.assertEqual(message.receiver_id, receiver.pk)
        self.assertFalse(Notification.objects.exists())

    def test_old_message_notifications_are_hidden_but_mentions_remain(self):
        from main.models import Notification
        user = Usuario.objects.create_user(username='receiver', email='receiver@example.test')
        Notification.objects.create(user=user, body='Mensagem antiga', linkzaocarai='messages/')
        Notification.objects.create(user=user, body='Menção preservada', linkzaocarai='sender/status/mention')
        self.client.force_login(user)
        response = self.client.get('/notifications/')
        self.assertNotContains(response, 'Mensagem antiga')
        self.assertContains(response, 'Menção preservada')

    def test_messages_are_ordered_chronologically_and_rendered_inline(self):
        from django.utils import timezone
        sender = Usuario.objects.create_user(username='sender', name='Sender User', email='sender@example.test')
        receiver = Usuario.objects.create_user(username='receiver', name='Receiver User', email='receiver@example.test')
        m1 = Message.objects.create(sender=sender, receiver=receiver, body='Primeira mensagem')
        m2 = Message.objects.create(sender=receiver, receiver=sender, body='Segunda mensagem')
        m3 = Message.objects.create(sender=sender, receiver=receiver, body='Terceira mensagem')

        self.client.force_login(receiver)
        response = self.client.get(f'/messages/{receiver.pk}-{sender.pk}')
        self.assertEqual(response.status_code, 200)

        chat_messages = list(response.context['chat_messages'])
        self.assertEqual([m.pk for m in chat_messages], [m1.pk, m2.pk, m3.pk])

        content = response.content.decode('utf-8')
        pos1 = content.find('Primeira mensagem')
        pos2 = content.find('Segunda mensagem')
        pos3 = content.find('Terceira mensagem')
        self.assertTrue(0 < pos1 < pos2 < pos3)

        t1 = timezone.localtime(m1.publishDate).strftime("%H:%M")
        t2 = timezone.localtime(m2.publishDate).strftime("%H:%M")
        self.assertIn(f'<div class="chat-bubble "><span class="chat-bubble-text">Primeira mensagem</span><time class="chat-bubble-time">{t1}</time></div>', content)
        self.assertIn(f'<div class="chat-bubble mine"><span class="chat-bubble-text">Segunda mensagem</span><time class="chat-bubble-time">{t2}</time></div>', content)
        self.assertNotIn(f'@{sender.username}:', content)
        self.assertNotIn(f'@{receiver.username}:', content)

        # Header beside avatar shows only name, without @username:
        self.assertIn(f'<a href="/{sender.username}/"><strong>Sender User</strong></a>', content)
        self.assertNotIn('Sender User @sender', content)

        self.client.force_login(sender)
        response_sender = self.client.get(f'/messages/{sender.pk}-{receiver.pk}')
        self.assertEqual(response_sender.status_code, 200)
        chat_messages_sender = list(response_sender.context['chat_messages'])
        self.assertEqual([m.pk for m in chat_messages_sender], [m1.pk, m2.pk, m3.pk])
        content_sender = response_sender.content.decode('utf-8')
        self.assertIn(f'<a href="/{receiver.username}/"><strong>Receiver User</strong></a>', content_sender)
        self.assertNotIn('Receiver User @receiver', content_sender)
