from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.shortcuts import get_object_or_404, render
from django.db.models import Q
from rest_framework import viewsets, generics

from .authentication import CustomTokenAuthentication
from .models import Message
from .serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# from channels.layers import get_channel_layer
from rest_framework import status
from rest_framework.decorators import api_view
from asgiref.sync import async_to_sync
from django.http import Http404, JsonResponse
from users.models import CustomUser


class MessageList(generics.ListAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    

class AllUserRoomMessages(APIView): 
    authentication_classes = [CustomTokenAuthentication]  
    permission_classes = [IsAuthenticated]

    def get(self, request, chat_id):
        user = request.user
        token = request.auth
        
        if user.token == token:
            chat = get_object_or_404(Chat, id=chat_id)
            messages = Message.objects.filter(chat__id=chat_id)
            mess_serializer = MessageSerializer(messages, many=True)
            chat_serializer = ChatSerializer(chat)
            print('chat_data ------------', chat.usernames())

            # Add usernames to the mess_serialized data
            for message_data in mess_serializer.data:
                print('chat_data ------------', message_data['user'])
                user_id = message_data['user']
                user = CustomUser.objects.get(id=user_id)
                message_data['username'] = user.username
                message_data['photo'] = f'/media/{user.photo}'

            return Response(
                {
                    "messages": mess_serializer.data,
                    "chat": chat_serializer.data,
                    "token": "Token is valid",
                    "users": chat.usernames(),
                    "photos": chat.user_info()
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"detail": "Token does not match."},
                status=status.HTTP_403_FORBIDDEN
            )
    

class CreateChatRoom(APIView):
    def post(self, request):

        authentication_classes = [CustomTokenAuthentication]  
        permission_classes = [IsAuthenticated]
        user = request.user
        token = request.auth

        if user.token == token:
            serializer = ChatSerializer(data=request.data)
            if serializer.is_valid():
                name = serializer.validated_data['name']
                users = serializer.validated_data['user']
                creater = users[0]
                print('ChatSerializer ------------------------------', name, users)

                # Create the Chat instance
                chat = Chat.objects.create(
                    name=name,
                    creater=creater.username
                    )

                # Add users to the chat
                chat.user.set(users)

                serializer = ChatSerializer(chat)  # Re-serialize the chat with user details

                return Response(
                    {
                        "chat": serializer.data,
                        "token": "Token is valid"
                    },
                    status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                {"detail": "Token does not match."},
                status=status.HTTP_403_FORBIDDEN
            )
    

class AllChatRooms(APIView):
    def get(self, request, user_id):

        authentication_classes = [CustomTokenAuthentication]  
        permission_classes = [IsAuthenticated]
        user = request.user
        token = request.auth

        if user.token == token:
            chats = Chat.objects.filter(user=user)
            serializer = ChatSerializer(chats, many=True)
            return Response(
                {
                    "chats": serializer.data,
                    "token": "Token is valid"
                },
                status=status.HTTP_201_CREATED
            )
        else:
            print('NOT TOKEN ------------------------------')
            return Response(
                {"detail": "AllChatRooms - Token does not match."},
                status=status.HTTP_403_FORBIDDEN
            )


class DeleteChatRoom(APIView):
    def get(self, request, chat_id):
        authentication_classes = [CustomTokenAuthentication]  
        permission_classes = [IsAuthenticated]
        user = request.user
        token = request.auth

        if user.token == token:
            chat = get_object_or_404(Chat, id=chat_id)
            chat.delete()

            return Response(
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                status=status.HTTP_403_FORBIDDEN
            )


class ConversationRoom(APIView):
    def post(self, request):
        authentication_classes = [CustomTokenAuthentication]  
        permission_classes = [IsAuthenticated]
        token = request.auth

        serializer = ConversationSerializer(data=request.data)

        if serializer.is_valid():
            users = serializer.validated_data['user']

            # Chek if the token is valid:
            if users[0].token == token:

                try:
                    conversation = Conversation.objects.filter(user=users[0]).filter(user=users[1]).first()
                except Conversation.DoesNotExist:
                    conversation = None
                if conversation is None:
                    conversation = Conversation.objects.create()

                    # Add users to the conversation
                    conversation.user.set(users)

                serializer = ConversationSerializer(conversation)  # Re-serialize the conversation with user details

                return Response(
                    {
                        "conversation": serializer.data,
                    },
                    status=status.HTTP_201_CREATED
                 )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class GetConversationView(APIView):
    def get(self, request, conv_id):
        authentication_classes = [CustomTokenAuthentication]  
        permission_classes = [IsAuthenticated]
        token = request.auth
        user = request.user

        if user.token == token:
            conversation = get_object_or_404(Conversation, id=conv_id)
            mess = Message.objects.filter(conversation=conversation)
            for m in mess:
                if m.user != user:
                    m.unread = False
                    m.save()
            mess_serializer = MessageSerializer(mess, many=True)

            # Add usernames to the serialized data
            for message_data in mess_serializer.data:
                user_id = message_data['user']
                user = CustomUser.objects.get(id=user_id)
                message_data['username'] = user.username
                message_data['photo'] = f'/media/{user.photo}'

            return Response(
                {
                    "conversation": mess_serializer.data,
                    "messages": mess_serializer.data  # Use the serialized data
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"detail": "Token does not match."},
                status=status.HTTP_403_FORBIDDEN
            )

class SaveMessage(APIView):
    def post(self, request):
        authentication_classes = [CustomTokenAuthentication]  
        permission_classes = [IsAuthenticated]
        resendMess = request.data.get('resendMess')
        conversation = request.data.get('conversation')
        resend = request.data.get('resend')
        message = get_object_or_404(Message, id=resendMess)
        conversation_ = get_object_or_404(Conversation, id=conversation)
        if resend:
            Message.objects.create(
                content=message,
                user=request.user,
                conversation=conversation_,
                )
        else:
            Message.objects.create(
                content=message,
                user=request.user,
                conversation=conversation_,
                )
        return Response(
                {"data": "ok"},
                status=status.HTTP_200_OK
            )


class DeleteUser(APIView):

    authentication_classes = [CustomTokenAuthentication]  
    permission_classes = [IsAuthenticated]

    def post(self, request):
        friendId = request.data['friend']
        userId = request.data['user']
        print('userId -----------------', userId)
        friend = get_object_or_404(CustomUser, id=friendId)
        user = get_object_or_404(CustomUser, id=userId)
        user.friends.remove(friend)
        user.save()
        return Response(
                {"data": "User has been deleted"},
                status=status.HTTP_200_OK
            ) 