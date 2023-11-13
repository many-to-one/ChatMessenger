from django.urls import re_path, path
from channels.routing import ProtocolTypeRouter, URLRouter
from . import consumers
from .sockets.friend_request import AllUsers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/conversation/(?P<room_name>\w+)/$', consumers.ConversationConsumer.as_asgi()),
    re_path(r'ws/AllUsers/', AllUsers.as_asgi()),
]
