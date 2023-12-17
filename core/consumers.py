import datetime
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from core import serializers
from users.models import CustomUser
from users.serializers import UserListSerializer
from .models import Chat, Conversation, Message
from channels.db import database_sync_to_async
from urllib.parse import parse_qs
from django.shortcuts import get_object_or_404
from django.core.serializers.json import DjangoJSONEncoder


class ChatConsumer(AsyncWebsocketConsumer):

    # When a WebSocket connection is established
    async def connect(self):

        # Get the chat room name from the URL
        self.room_name = self.scope['url_route']['kwargs']['room_name']

        # Extract the token and userId from the query parameters
        query_string = self.scope['query_string'].decode('utf-8')
        query_params = parse_qs(query_string)

        # Get the token and userId from the query parameters
        token = query_params.get('token', [''])[0]
        userId = query_params.get('userId', [''])[0]

        # Create a group name for this chat room
        self.room_group_name = '%s' % self.room_name
        print('self.room_group_name ---------------', self.room_group_name)

        # Add the WebSocket channel to the group associated with the chat room
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        user = await self.checkUser(userId, token)
        if user:
            # Accept the WebSocket connection
            await self.accept()
            print('connect ---------------- ')
        else:
            await self.close()


    
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
        if message_type == 'new_message':
            message = text_data_json['message']
            chatID = text_data_json['id']
        
            # Extract the token and userId from the query parameters
            query_string = self.scope['query_string'].decode('utf-8')
            query_params = parse_qs(query_string)

            # Get the userId from the query parameters
            userId = query_params.get('userId', [''])[0]

            mess = await self.save_mess(message, userId, chatID)
            # Send the message to the chat room group (async def chatroom_message(self, event))
            await self.channel_layer.group_send(
                self.room_group_name, 
                {
                    'type': 'chatroom_message', 
                    'id': mess.id, 
                    'message': mess.content,
                    'username': mess.user.username,
                    'user_id': mess.user.id,
                    'photo': f'/media/{mess.user.photo}',
                    'unread': mess.unread,
                    'chat_id': mess.chat.id,
                    'timestamp': mess.timestamp,
                }
            )

        # Delete message logic
        # message_type = text_data_json.get('type', '')
        if message_type == 'delete_message':

            # Handle delete message request
            mess = await self.delete_message(text_data_json['message_id'], text_data_json['user_id'])
            if mess != False:
                await self.channel_layer.group_send(
                    self.room_group_name, 
                    {'type': 'delete_message_from', 
                     'message_id': text_data_json['message_id'],
                     'user_id': text_data_json['user_id'],
                    }
                )


        # Add new users to the chat
        if message_type == 'add_users':
            users = await self.addUsers(text_data_json['users'], text_data_json['chatId'])
            print('NEW_USERS ----------------------', users)
            if users != False:
                for user in users:
                    await self.channel_layer.group_send(
                    self.room_group_name, 
                    {'type': 'new_chatUsers', 
                     'users': text_data_json['users'],
                     'id': user.id,
                     'username': user.username,
                     'photo': f'/media/{user.photo}',
                    }
                )
                    
        # Delete user from chat logic
        if message_type == 'delete_user':
            print('delete_user ----------------', text_data_json)
            # Handle delete message request
            result = await self.delete_user(text_data_json['user_id'], text_data_json['chatId'])
            if result != False:
                await self.channel_layer.group_send(
                    self.room_group_name, 
                    {'type': 'delete_user_from', 
                     'chatId': text_data_json['chatId'],
                     'user_id': text_data_json['user_id'],
                    }
                )


    # Save messages to the database
    @database_sync_to_async
    def save_mess(self, message, userId, chatID):
        user = get_object_or_404(CustomUser, id=userId)
        chat = get_object_or_404(Chat, id=chatID)
        mess = Message.objects.create(
            content=message,
            user=user,
            chat=chat
        )
        mess.save()
        return mess
    
    # When a message is received by the chat room group
    async def chatroom_message(self, event):

        # Get the message from the event
        message = event['message']
        id = event['id']
        username = event['username']
        user_id = event['user_id']
        photo = event['photo']
        unread = event['unread']
        chat_id = event['chat_id']
        timestamp = event['timestamp']

        # Get all messages asynchronously
        await self.send(
            text_data=json.dumps({
                'type': 'added_message',
                'message': message,
                'id': id,
                'username': username,
                'user_id': user_id,
                'photo': photo,
                'unread': unread,
                'chat_id': chat_id,
                'timestamp': timestamp,
            })
        )
    
    
    # Delete message
    @database_sync_to_async
    def delete_message(self, message_id, user_id):
        try:
            message = Message.objects.get(id=message_id)
        except Exception as e:
            print('ERROR -------------------------', e)

        # Delete message if it user's message
        if message.user.id == int(user_id):
            message.delete()
            self.send(text_data=json.dumps({
                'type': 'message_deleted',
                'message_id': message_id
            }))
            return message_id
        else:
            # If not - return False
            return False
        
    # Send data to the chat after deleting the message
    async def delete_message_from(self, event):

        # Get the message from the event
        id = event['message_id']
        user_id = event['user_id']

        # Get all messages asynchronously
        await self.send(
            text_data=json.dumps({
                'id': id,
                'type': 'message_deleted'
            })
        )
        

    # Add new chat users to the database
    @database_sync_to_async
    def addUsers(self, users, chatId):
        users_to_add = CustomUser.objects.filter(id__in=users)
        chat = get_object_or_404(Chat, id=chatId)
        chat.user.add(*users_to_add)
        chat.save()
        print('users_to_add ---------------------', users_to_add)
        print('users_to_add ---------------------', chat)
        return users_to_add
    
    async def new_chatUsers(self, event):

        # Get the message from the event
        users = event['users']
        id = event['id']
        username = event['username']
        photo = event['photo']

        # Get all messages asynchronously
        await self.send(
            text_data=json.dumps({
                'type': 'added_users',
                'users': users,
                'id': id,
                'username': username,
                'photo': photo,
            })
        )

    # Delete chat user from the database
    @database_sync_to_async
    def delete_user(self, userId, chatId):
        chat = get_object_or_404(Chat, id=chatId)
        user = get_object_or_404(CustomUser, id=userId)
        chat.user.remove(user)
        return True
    
    # Send data to the chat after deleting the user
    async def delete_user_from(self, event):

        user_id = event['user_id']
        chatId = event['chatId']

        await self.send(
            text_data=json.dumps({
                'user_id': user_id,
                'chatId': chatId,
                'type': 'user_deleted',
            })
        )


class ConversationConsumer(AsyncWebsocketConsumer):

    conver = None
    usr = None

    # When a WebSocket connection is established
    async def connect(self):

        print('connect trying -----------------------')


        # Get the chat room name from the URL
        self.room_name = self.scope['url_route']['kwargs']['room_name']

        # Extract the token and userId from the query parameters
        query_string = self.scope['query_string'].decode('utf-8')
        query_params = parse_qs(query_string)

        # Get the token and userId from the query parameters
        # token = query_params.get('token', [''])[0]
        token = 'test without token'
        userId = query_params.get('userId', [''])[0]
        # receiverId = query_params.get('receiverId', [''])[0]

        # Create a group name for this chat room
        self.room_group_name = '%s' % self.room_name
        print('self.room_group_name ---------------', self.room_group_name)

        # Add the WebSocket channel to the group associated with the chat room
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        user = await self.checkUser(userId, token, self.room_group_name)
        if user:
            # Accept the WebSocket connection
            await self.accept()
            print('connect ---------------- ')
        else:
            print('connect unsuccessful ---------------- ')
            await self.close()


    
    @database_sync_to_async
    def checkUser(self, userId, token, conv):
        try:
            user = CustomUser.objects.get(
                id=userId
            )
            # if user.token == token:
            mess = Message.objects.filter(
                conversation=conv, 
                user=user,
                unread=True,
                )
            for m in mess:
                m.unread = False
                m.save()
            print('checkUser -------------------------', user.token)
            return user
            # else:
            #     print('checkUser else -------------------------', user.token)
            #     return None
        except CustomUser.DoesNotExist:
            return None
        

    # When a WebSocket connection is closed
    async def disconnect(self, code):

        # Remove the WebSocket channel from the chat room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        print('disconnect ---------------- ')
        await self.close()

    Unread = None
    # When a message is received from the WebSocket
    async def receive(self, text_data):

        # Parse the incoming JSON message
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type', '')


        if message_type == 'unread':
            messageId = text_data_json['message']
            chatID = text_data_json['id']
            mess = await self.markAsRead(messageId)
            print('UNREAD @@@@@@@@@@@@@', mess.id, mess.user.username)
            await self.channel_layer.group_send(
                self.room_group_name, 
                {
                    'type': 'chatroom_message_read', 
                    'id': mess.id, 
                    'content': mess.content,
                    'username': mess.user.username,
                    'user_id': mess.user.id,
                    'unread': mess.unread,
                    'timestamp': json.dumps(mess.timestamp, cls=DjangoJSONEncoder),
                    'photo': f'/media/{mess.user.photo}',
                    'conversation_id': chatID,
                }
            )


        if message_type == 'on_page':
            userId = text_data_json['userId']
            await self.channel_layer.group_send(
                self.room_group_name, 
                {
                    'type': 'on_page_response',
                    'userId': userId
                }
            )


        if message_type == 'new_message':
            message = text_data_json['message']
            chatID = text_data_json['id']
            receiverId = text_data_json['receiverId']
        
            # Extract the token and userId from the query parameters
            query_string = self.scope['query_string'].decode('utf-8')
            query_params = parse_qs(query_string)

            # Get the userId from the query parameters
            userId = query_params.get('userId', [''])[0]
            # receiverId = query_params.get('receiverId', [''])[0]

            mess = await self.save_mess(message, userId, chatID, receiverId)
            # mess = await self.save_mess(message, userId, receiverId)

            # Send the message to the chat room group (async def chatroom_message(self, event))
            await self.channel_layer.group_send(
                self.room_group_name, 
                {
                    'type': 'chatroom_message', 
                    'id': mess.id, 
                    'content': mess.content,
                    'username': mess.user.username,
                    'user_id': mess.user.id,
                    'unread': mess.unread,
                    'timestamp': json.dumps(mess.timestamp, cls=DjangoJSONEncoder),
                    'photo': f'/media/{mess.user.photo}',
                    'conversation_id': chatID,
                }
            )
            print('unread @@@@@@@@@@@@@', mess.unread)

        # Delete message logic
        if message_type == 'delete_message':

            # Handle delete message request
            mess = await self.delete_message(text_data_json['message_id'], text_data_json['user_id'])
            if mess != False:
                await self.channel_layer.group_send(
                    self.room_group_name, 
                    {'type': 'delete_message_from', 
                     'message_id': text_data_json['message_id'],
                     'user_id': text_data_json['user_id'],
                    }
                )

        if message_type == 'resend_message':
            message = text_data_json['message']
            chatID = text_data_json['id']
            # print('RESEND_MESS @@@@@@@@@@@@@@', message, chatID)
            mess = await self.resend_mess(message, chatID)
            print('RESEND_MESS @@@@@@@@@@@@@@', mess)
            await self.channel_layer.group_send(
                self.room_group_name, 
                {
                    'type': 'resend_message_', 
                    'id': mess.id, 
                    'content': mess.content,
                    'username': mess.user.username,
                    'unread': mess.unread,
                    'timestamp': json.dumps(mess.timestamp, cls=DjangoJSONEncoder),
                }
            )


    async def on_page_response(self, event):
        userId = event['userId']

        await self.send(
            text_data=json.dumps({
                'type': 'on_page_response',
                'userId': userId,
            })
        )


    async def type_response(self, event):
        receiverId = event['id']

        await self.send(
            text_data=json.dumps({
                'type': 'type_response',
                'receiverId': receiverId,
            })
        )
    

    async def chatroom_message_read(self, event):

        # Get the message from the event
        message = event['content']
        id = event['id']
        username = event['username']
        user_id = event['user_id']
        unread = event['unread']
        photo = event['photo']
        conversation_id = event['conversation_id']
        timestamp = event['timestamp']

        # Get all messages asynchronously
        await self.send(
            text_data=json.dumps({
                'type': 'chatroom_message_read',
                'content': message,
                'id': id,
                'username': username,
                'user_id': user_id,
                'unread': unread,
                'photo': photo,
                'conversation_id': conversation_id,
                'timestamp': timestamp,
            })
        )
        
    # When a message is received by the chat room group
    async def chatroom_message(self, event):

        # Get the message from the event
        message = event['content']
        id = event['id']
        username = event['username']
        user_id = event['user_id']
        unread = event['unread']
        photo = event['photo']
        conversation_id = event['conversation_id']
        timestamp = event['timestamp']

        # Get all messages asynchronously
        await self.send(
            text_data=json.dumps({
                'type': 'received_message',
                'content': message,
                'id': id,
                'username': username,
                'user_id': user_id,
                'unread': unread,
                'photo': photo,
                'conversation_id': conversation_id,
                'timestamp': timestamp,
            })
        )

    # Send data to the chat by deleting the message
    async def delete_message_from(self, event):

        # Get the message from the event
        id = event['message_id']
        user_id = event['user_id']

        # Get all messages asynchronously
        await self.send(
            text_data=json.dumps({
                'id': id,
                'type': 'message_deleted'
            })
        )

    # Send data to the chat by deleting the message
    async def resend_message_(self, event):

         # Get the message from the event
        message = event['content']
        id = event['id']
        username = event['username']
        # resend = event['resend']
        unread = event['unread']
        timestamp = event['timestamp']

        # Get all messages asynchronously
        await self.send(
            text_data=json.dumps({
                'content': message,
                'id': id,
                'username': username,
                # 'resend': resend,
                'unread': unread,
                'timestamp': timestamp,
                'type': 'resend_message_'
            })
        )


    @database_sync_to_async
    def markAsRead(self, mess):
        message = get_object_or_404(Message, id=mess)
        message.unread = True
        message.save()
        print('markAsRead @@@@@@@@@@@@@@@', message.id, message.user.username, message.content)
        return message
    

    # Save messages to the database
    @database_sync_to_async
    def save_mess(self, message, userId, chatID, receiverId):
        conversation = get_object_or_404(Conversation, id=chatID)
        user = get_object_or_404(CustomUser, id=userId)
        receiver = get_object_or_404(CustomUser, id=receiverId)
        mess = Message.objects.create(
                    content=message,
                    user=user,
                    conversation=conversation,
                    unread=True,
                )
        mess.save()
        print('USER - 2 @@@@@@@@@@@@@', userId, chatID, mess.id, mess.unread, mess.user.username, mess.content)
        return mess
    
    # Delete message
    @database_sync_to_async
    def delete_message(self, message_id, user_id):
        try:
            message = Message.objects.get(id=message_id)
        except Exception as e:
            print('ERROR -------------------------', e)

        # Delete message if it user's message
        if message.user.id == int(user_id):
            message.delete()
            self.send(text_data=json.dumps({
                'type': 'message_deleted',
                'message_id': message_id
            }))
            return message_id
        else:
            # If not - return False
            return False
        

    # Get message to resend
    @database_sync_to_async
    def resend_mess(self, message, chatID):
        mess = get_object_or_404(Message, id=message)
        conversation = get_object_or_404(Conversation, id=chatID)
        new_mess = Message.objects.create(
            user=mess.user,
            content=mess.content,
            conversation=conversation,
            resend=True,
        )
        new_mess.save()
        print('new_mess --------**********************-----------------', new_mess)
        return new_mess