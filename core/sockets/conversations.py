import datetime
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from core import serializers
from users.models import CustomUser
from users.serializers import UserListSerializer
from ..models import Chat, Conversation, Message
from channels.db import database_sync_to_async
from urllib.parse import parse_qs
from django.shortcuts import get_object_or_404


class ConversationConsumer(AsyncWebsocketConsumer):

    # When a WebSocket connection is established
    async def connect(self):
        # Extract the token and userId from the query parameters
        query_string = self.scope['query_string'].decode('utf-8')
        query_params = parse_qs(query_string)

        # Get the token and userId from the query parameters
        token = query_params.get('token', [''])[0]
        userId = query_params.get('userId', [''])[0]
        receiverId = query_params.get('receiverId', [''])[0]
        print('RESEND SOCKET USERS -----------------------', userId, receiverId)

        user = await self.checkUser(userId, token)
        if user:
            await self.accept()
            print('ConversationConsumer connect ---------------- ')
            # await self.send(json.dumps(
            #     {
            #         'type': 'allUsers',
            #     }
            # ))

        else:
            await self.close()
            print('ConversationConsumer close -----------------------')



    @database_sync_to_async
    def checkUser(self, userId, token):
        try:
            user = CustomUser.objects.get(
                id=userId
            )
            if user.token == token:
                return user
            else:
                return None
        except CustomUser.DoesNotExist:
            return None