from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/messages/(?P<senderid>[0-9a-fA-F-]{36})-(?P<receiverid>[0-9a-fA-F-]{36})/', consumers.ChatConsumer.as_asgi()),
]