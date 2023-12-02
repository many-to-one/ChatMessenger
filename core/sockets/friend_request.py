import datetime
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from core import serializers
from users.models import CustomUser
from users.serializers import UserListSerializer
from ..models import BlockedUsers, Chat, Conversation, IncomingFriendRequest, Message, OutcomingFriendRequest
from channels.db import database_sync_to_async
from urllib.parse import parse_qs
from django.shortcuts import get_object_or_404


class AllUsers(AsyncWebsocketConsumer):
    async def connect(self):

        # Extract the token and userId from the query parameters
        query_string = self.scope['query_string'].decode('utf-8')
        query_params = parse_qs(query_string)

        # Get the token and userId from the query parameters
        token = query_params.get('token', [''])[0]
        userId = query_params.get('userId', [''])[0]
        print('COUNT SOCKET USER -----------------------', userId)

        user = await self.checkUser(userId, token)
        if user:
            # Accept the WebSocket connection
            await self.accept()
            print('connect ---------------- ')
            friends_count = await self.friends_count(userId)  
            incomingFriendRequest = await self.getIncomingFriendRequest(userId)
            outComingFriendRequest = await self.getOutComingFriendRequest(userId)
            # myFriends = await self.myFriends(userId)
            findFriends = await self.findFriends(userId)
            # await self.send(json.dumps(users))
            await self.send(json.dumps(
                {
                    'type': 'allUsers',
                    'friends_count': friends_count,
                    'incomingFriendRequest': incomingFriendRequest,
                    'outComingFriendRequest': outComingFriendRequest,
                    # 'myFriends': myFriends,
                    'findFriends': findFriends,
                }
            ))

        else:
            await self.close()
        # Accept the WebSocket connection
        # self.accept()

        print('FriendRequest CONNECT -----------------------')


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


    @database_sync_to_async
    def findFriends(self, userId):
        req_data = []
        user = get_object_or_404(CustomUser, id=userId)
        friends = user.friends.values_list('id', flat=True)
        blocked_users_ids = BlockedUsers.objects.filter(user=user).values_list('blockedUsers', flat=True)
        print('blocked_users_ids ---------------------------', blocked_users_ids)
        users = CustomUser.objects.exclude(id__in=friends).exclude(id=userId).exclude(id__in=blocked_users_ids)
        for u in users:
            req_data.append(
                serializers.FriendListSerializer(u).data
            )
        
        return req_data
        
        

    # @database_sync_to_async
    # def myFriends(self, userId):
    #     req_data = []
    #     user = get_object_or_404(CustomUser, id=userId)
    #     try:
    #         incomingFriendRequest = get_object_or_404(IncomingFriendRequest, user=user)
    #         inUsers = incomingFriendRequest.inUsers.all()
    #         if inUsers:    
    #             print('GET INCOMING getIncomingFriendRequest ----------------', inUsers)            
    #             for u in inUsers:
    #                 req_data.append(serializers.FriendListSerializer(u).data)
    #     except Exception:
    #         return []

    #     return req_data
        

    @database_sync_to_async
    def getIncomingFriendRequest(self, userId):
        req_data = []
        user = get_object_or_404(CustomUser, id=userId)
        try:
            incomingFriendRequest = get_object_or_404(IncomingFriendRequest, user=user)
            inUsers = incomingFriendRequest.inUsers.all()
            if inUsers:    
                print('GET INCOMING getIncomingFriendRequest ----------------', inUsers)            
                for u in inUsers:
                    req_data.append(serializers.FriendListSerializer(u).data)
        except Exception:
            return []

        return req_data
        

    @database_sync_to_async
    def getOutComingFriendRequest(self, userId):
        req_data = []
        user = get_object_or_404(CustomUser, id=userId)
        try:
            outcomingFriendRequest = get_object_or_404(OutcomingFriendRequest, user=user)
            print('outcomingFriendRequest ----------------', outcomingFriendRequest)
            outUsers = outcomingFriendRequest.outUsers.all()
            print('outUsers ----------------', outUsers)
            if outUsers:    
                print('GET INCOMING getIncomingFriendRequest ----------------', outUsers)            
                for u in outUsers:
                    req_data.append(serializers.FriendListSerializer(u).data)
        except Exception:
            return []

        return req_data


    @database_sync_to_async
    def friends_count(self, userId):
        user = get_object_or_404(CustomUser, id=userId)
        friends_count = user.friends.all().exclude(id=userId)
        
        return {
            'count': friends_count.count(),
        }
    

    # Send data to the clien side
    # async def friends_count_(self, event):

    #     friends_count = event['friends_count']

    #     await self.send(
    #         text_data=json.dumps({
    #             'friends_count': friends_count,
    #             # 'type': 'users'
    #         })
    #     )

    @database_sync_to_async
    def getUser(self, userId, requestId):
        user = get_object_or_404(CustomUser, id=userId)
        requestUser = get_object_or_404(CustomUser, id=requestId)

        from django.db.models import Q
        hasConv = Conversation.objects.filter(
            Q(user=user) & Q(user=requestUser)
        )

        if hasConv:
            last_mess = Message.objects.filter(
                    conversation=hasConv,
                ).last()
            last_mess_data = {
                'content': f'{last_mess.content[0:20]} ...', 
                'timestamp': last_mess.timestamp.strftime('%Y-%m-%d'),  
                'unread': last_mess.unread,
            }

            return {
                'id': requestUser.id,
                'username': requestUser.username,
                'photo': f'/media/{requestUser.photo}',
                'count': 0,
                'last_mess': last_mess_data,
                'conv': conv.id,
            }

        else:
            conv = Conversation.objects.create()
            conv.user.add(requestUser, userId)
            conv.save()
            # conv_serializer = serializers.Conv(conv)
            last_mess_data = {  # Always ensure it's initialized
                'content': '', 
                'timestamp': '',
                'unread': '',
            }

            return {
                'id': requestUser.id,
                'username': requestUser.username,
                'photo': f'/media/{requestUser.photo}',
                'count': 0,
                'last_mess': last_mess_data,
                'conv': conv.id,
            }



    @database_sync_to_async
    def getUsers(self, requestId):
        from django.db.models import Q
        user1 = get_object_or_404(CustomUser, id=requestId)
        # users = CustomUser.objects.all().exclude(id=userId)
        user_ = user1.friends.all().exclude(id=requestId).order_by('id').last()

        user_data = []

        last_mess_data = {  # Always ensure it's initialized
            'content': '', 
            'timestamp': '',
            'unread': '',
        }

        # for user in users:
        user2 = get_object_or_404(CustomUser, id=user_.id)
        conversation1 = Conversation.objects.filter(user=user1)
        conversation2 = Conversation.objects.filter(user=user_)
        # Find the common conversations
        common_conversations = conversation1.filter(id__in=conversation2)
        if common_conversations:
            for conv in common_conversations:
                unread_count = Message.objects.filter(
                    user=user2,
                    conversation=conv,
                    unread=True,
                ).count()
                last_mess = Message.objects.filter(
                    conversation=conv,
                ).last()
                if last_mess is not None:
                    last_mess_data = {
                        'content': f'{last_mess.content[0:20]} ...', 
                        'timestamp': last_mess.timestamp.strftime('%Y-%m-%d'),  
                        'unread': last_mess.unread,
                    }
                else:
                    last_mess_data = {
                        'content': '', 
                        'timestamp': '',
                        'unread': '',
                    }
                conv = conv.id
                
        else:
            unread_count=0
            conv=None
            last_mess_data = {
                'content': '', 
                'timestamp': '',
                'unread': '',
            }
        user_data.append({
            'id': user_.id,
            'username': user_.username,
            'photo': f'/media/{user_.photo}',
            'count': unread_count,
            'last_mess': last_mess_data,
            'conv': conv,
        })
                    
        return user_data[0]
    
    # Send data to the clien side
    # async def users_(self, event):

    #     # unread_count = event['unread_count']
    #     users = event['users']

    #     await self.send(
    #         text_data=json.dumps({
    #             # 'unread_count': unread_count,
    #             'users': users,
    #             'type': 'users'
    #         })
    #     )
        



    async def disconnect(self, code):
        print('disconnect ---------------- ')
        await self.close()

###############################################################################################################
################################################## RESEIVE ####################################################
###############################################################################################################


    # When a message is received from the WebSocket
    async def receive(self, text_data):

        # Parse the incoming JSON message
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type', '')

        if message_type == 'getAllUsers':
            users = CustomUser.objects.all()
            print('RECEIVE text_data_json -----------------------', text_data_json)
            userId = text_data_json['userId']
            conversationId = text_data_json['conversationId']
            count = await self.unread_count(userId, conversationId)
            print('RECEIVE COUNT -----------------------', text_data_json)
            await self.channel_layer.group_send(
                self.room_group_name, 
                {
                    'type': 'unread_count_', 
                    'count': count, 
                    'users': users,
                }
            )


        elif message_type == 'friendRequest':
            requestId = text_data_json.get('requestId', '')
            userId = text_data_json.get('userId', '')
            res = await self.addFriendRequest(requestId, userId)
            print('RECEIVE addFriend -----------------------', res)
            if res:
                await self.send(
                    text_data=json.dumps({
                        'type': 'addFriend',
                        'response': 'ok',
                        'request': res,
                    })
                )


        elif message_type == 'confirmRequest':
            userId = text_data_json.get('userId', '')
            requestId = text_data_json.get('requestId', '')
            res = await self.confirmRequest(userId, requestId)
            user = await self.getUser(userId, requestId)

            print('confirmRequest ---------------------', userId, requestId)

            if res == True:
                # users = await self.getUsers(userId)
                await self.send(
                    text_data=json.dumps({
                        'type': 'confirmRequest',
                        'response': 'ok',
                        'user': user,
                    })
                )


        elif message_type == 'denyRequest':
            userId = text_data_json.get('userId', '')
            requestId = text_data_json.get('requestId', '')
            res = await self.denyRequest(userId, requestId)
            if res == True:
                await self.send(
                    text_data=json.dumps({
                        'type': 'denyResponse',
                        'response': 'ok',
                    })
                )

            
        elif message_type == 'blockUser':
            userId = text_data_json.get('userId', '')
            requestId = text_data_json.get('requestId', '')
            res = await self.blockRequest(userId, requestId)
            if res == True:
                await self.send(
                    text_data=json.dumps({
                        'type': 'blockResponse',
                        'response': 'ok',
                    })
                )


    @database_sync_to_async
    def blockRequest(self, userId, requestId):
        user = get_object_or_404(CustomUser, id=userId)
        reqUser = get_object_or_404(CustomUser, id=requestId)
        block, created = BlockedUsers.objects.get_or_create(
            user=reqUser
        )
        block.blockedUsers.add(user)
        block.save()
        out = get_object_or_404(OutcomingFriendRequest, user=reqUser)
        out.outUsers.remove(user)
        out.save()
        in_ = get_object_or_404(IncomingFriendRequest, user=user)
        in_.inUsers.remove(reqUser)
        in_.save()
        return True



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
    

    @database_sync_to_async
    def confirmRequest(self, userId, requestId):
        user = get_object_or_404(CustomUser, id=userId)
        friend = get_object_or_404(CustomUser, id=requestId)
        user.friends.add(friend)
        out = OutcomingFriendRequest.objects.get(
            user=friend,
        )
        try:
            out.outUsers.remove(user)
            out.save()
        except Exception as e:
            print('Exception ----------------------', e)
        in_ = IncomingFriendRequest.objects.get(
            user=user,
        )
        in_.inUsers.remove(friend)
        in_.save()
        print('ALL FRIENDS -----------------------', user.friends.all())
        return True
    

    @database_sync_to_async
    def denyRequest(self, userId, requestId):
        user = get_object_or_404(CustomUser, id=userId)
        reqUser = get_object_or_404(CustomUser, id=requestId)
        out = get_object_or_404(OutcomingFriendRequest, user=reqUser)
        out.outUsers.remove(user)
        out.save()
        in_ = get_object_or_404(IncomingFriendRequest, user=user)
        in_.inUsers.remove(reqUser)
        in_.save()
        return True
        


    @database_sync_to_async
    def unread_count(self, userId, conversationId):
        user = get_object_or_404(CustomUser.objects.select_related('message_set'), id=userId)
        conversation = get_object_or_404(Conversation, id=conversationId)
        unread_message_count = user.message_set.filter(
            unread=True,
            conversation=conversation,
            ).count() 
        return unread_message_count
    

    # Send data to the clien side
    async def unread_count_(self, event):

        unread_count = event['unread_count']
        users = event['users']

        await self.send(
            text_data=json.dumps({
                'unread_count': unread_count,
                'users': users,
            })
        )