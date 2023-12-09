import datetime
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from core import serializers
from users.models import CustomUser
from users.serializers import UserListSerializer
from ..models import Chat, Conversation, IncomingFriendRequest, Message, OutcomingFriendRequest
from channels.db import database_sync_to_async
from urllib.parse import parse_qs
from django.shortcuts import get_object_or_404
from django.core.serializers.json import DjangoJSONEncoder


class AddFriendCon(AsyncWebsocketConsumer):

    # When a WebSocket connection is established
    async def connect(self):

        print('AddFriendCon -------connect trying -----------------------')

        # Get the chat room name from the URL
        self.room_name = self.scope['url_route']['kwargs']['room_name']

        # Extract the token and userId from the query parameters
        query_string = self.scope['query_string'].decode('utf-8')
        query_params = parse_qs(query_string)

        # Get the token and userId from the query parameters
        token = query_params.get('token', [''])[0]
        userId = query_params.get('userId', [''])[0]
        # receiverId = query_params.get('receiverId', [''])[0]
        # print('RESEND SOCKET USERS -----------------------', userId, receiverId)

        # Create a group name for this chat room
        self.room_group_name = '%s' % self.room_name
        print('self.room_group_name ---------------', self.room_group_name)

        # Add the WebSocket channel to the group associated with the chat room
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        user = await self.checkUser(userId, token)
        if user:
            # Accept the WebSocket connection
            await self.accept()
            print('AddFriendCon @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ ')
        else:
            print('connect unsuccessful ---------------- ')
            await self.close()


    @database_sync_to_async
    def checkUser(self, userId, token):
        try:
            user = CustomUser.objects.get(
                id=userId
            )
            if user.token == token:
                print('checkUser -------------------------', user.token)
                return user
            else:
                print('checkUser else -------------------------', user.token)
                return None
        except CustomUser.DoesNotExist:
            return None
        

    # When a WebSocket connection is closed
    async def disconnect(self, code):

        # Remove the WebSocket channel from the chat room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        print('disconnect ---------------- ')
        await self.close()


    # When a message is received from the WebSocket
    async def receive(self, text_data):

        # Parse the incoming JSON message
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type', '')

        if message_type == 'test':
            # requestId = text_data_json.get('requestId', '')
            # userId = text_data_json.get('userId', '')
            # res = await self.addFriendRequest(requestId, userId)
            # print('RECEIVE addFriend -----------------------', res)
            # if res:
            #     await self.send(
            #         text_data=json.dumps({
            #             'type': 'add_Friend',
            #             'response': 'ok +++',
            #             'request': res,
            #         })
            #     )
            print('test get @@@@@@@@@@@@@@@@@@@@@@@@ ')
            await self.send(
                    text_data=json.dumps({
                        'type': 'add_Friend',
                        'response': 'ok +++',
                    })
                )

    @database_sync_to_async
    def addFriendRequest(self, requestId, userId):
        req_data = []
        user = get_object_or_404(CustomUser, id=userId)
        reqUser = get_object_or_404(CustomUser, id=requestId)
        out, created = OutcomingFriendRequest.objects.get_or_create(user=user)
        # if created:
        out.outUsers.add(reqUser)
        out.save()
        print('addFriendRequest out -----------------------', out)
        in_, created = IncomingFriendRequest.objects.get_or_create(user=reqUser)
        # if created:
        in_.inUsers.add(user)
        in_.save()
        print('addFriendRequest in -----------------------', in_)
        for u in out.outUsers.all():
            req_data.append(
                serializers.FriendListSerializer(u).data
            )
        return req_data
        

    # When a message is received by the chat room group
    # async def add_Friend(self, event):
    #     # Get the message from the event
    #     request = event['request']
    #     # Get all messages asynchronously
    #     await self.send(
    #         text_data=json.dumps({
    #             'request': request,
    #         })
    #     )
