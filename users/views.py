import json
from django.shortcuts import get_object_or_404
from rest_framework import generics   
from rest_framework.views import APIView
from uuid import uuid4
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import logout
from django.utils import timezone
from core.authentication import CustomTokenAuthentication

from .models import (
    CustomUser,
    BlackListToken
)

from core.models import (
    Conversation,
    Message,
    )

from .serializers import (
    AccessTokenSerializer,
    RegisterSerializer,
    LoginSerializer,
    UserListSerializer,
)


class UserRegistrationView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            password = serializer.validated_data['password']
            user = request.user
            user.set_password(password)
            user.save()
            return Response(
                    {
                        'message': 'Success',
                        'user_id': user.id,
                    }, 
                    status=status.HTTP_200_OK
                )


class LoginView(APIView):
    def post(self, request):
        token = request.auth
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            login_at = timezone.now()

            try:
                user = CustomUser.objects.get(email=email)
                if not user:
                    return Response({'message': 'Incorrect email'}, status=status.HTTP_400_BAD_REQUEST)
                if not user.check_password(password):
                    # raise AuthenticationFailed('Incorrect password!')
                    return Response({'message': 'Incorrect password'}, status=status.HTTP_400_BAD_REQUEST)
            except CustomUser.DoesNotExist:
                return Response({'error': 'Invalid email or password'}, status=status.HTTP_400_BAD_REQUEST)    
        
            if user:                    
                # If the user exists, create a token
                user.token = token
                user.access_token = f'{uuid4()}{uuid4()}{uuid4()}'
                user.is_logged = True
                user.login_at = login_at
                user.save()
                # login(request, user)

                return Response(
                    {
                        'message': 'Success',
                        'email': user.email,
                        'username': user.username,
                        'id': user.id,
                        'token': user.token,
                        'access_token': user.access_token,
                        'photo': f'/media/{user.photo}'
                    }, 
                    status=status.HTTP_200_OK
                )
        
        # If the serializer is not valid, return a bad request response
        return Response(
                {'message': 'Wrong data'},
                status=status.HTTP_400_BAD_REQUEST
        )


class LogoutView(APIView):
    authentication_classes = [CustomTokenAuthentication]  
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.auth

        # Assuming you have a user object available in the request
        userId = request.data.get('userId')
        user = get_object_or_404(CustomUser, id=userId)

        # Check if the user has a token
        if user:
            BlackListToken.objects.create(
                token=token,
                user=user,
            )
            # Create a new token value for the user
            user.token = ''
            user.is_logged = False
            # user.is_authenticated = False
            user.save()
            logout(request)
            print('LOG OUT auth -------------------------------')

            return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Error'}, status=status.HTTP_403_FORBIDDEN)
        

class FriendListView(APIView):
    authentication_classes = [CustomTokenAuthentication]  
    permission_classes = [IsAuthenticated]

    def get(self, request):
        token = request.auth
        user = request.user

        if user.token == token:
            friends = user.friends.all().exclude(id=user.id)
            print('FRIENDS --------------------', friends)

            user_data = []

            last_mess_data = {  # Always ensure it's initialized
                'content': '', 
                'timestamp': '',
                'unread': '',
            }

            for user in friends:
                user2 = get_object_or_404(CustomUser, id=user.id)
                conversation1 = Conversation.objects.filter(user=user)
                conversation2 = Conversation.objects.filter(user=user2)
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
                    
                    user_data.append({
                        'id': user.id,
                        'username': user.username,
                        'photo': f'/media/{user.photo}',
                        'count': unread_count,
                        'last_mess': last_mess_data,
                        'conv': conv,
                    })
                     
                else:
                    unread_count=0
                    user_data.append({
                     'id': user.id,
                     'username': user.username,
                     'photo': f'/media/{user.photo}',
                     'count': unread_count,
                     'last_mess': last_mess_data,
                     'conv': conv,
                 })

            return Response(
                {
                    'user_data': user_data,
                    "token": "Token is valid"
                },
                status=status.HTTP_200_OK
            )



class UserListView(APIView):
    authentication_classes = [CustomTokenAuthentication]  
    permission_classes = [IsAuthenticated]

    def get(self, request):
        token = request.auth
        # userId = request.META.get("HTTP_USERID")
        # user = get_object_or_404(CustomUser, id=int(userId))
        user = request.user

        # Check if user token is the same with token from the client side
        if user.token == token:
            users = CustomUser.objects.all().exclude(id=user.id)
            serializer = UserListSerializer(users, many=True)
            return Response(
                {
                    'users': serializer.data,
                    "token": "Token is valid"
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"detail": "Token does not match."},
                status=status.HTTP_403_FORBIDDEN
            )
    
    def post(self, request):
        exclude_ids = request.data['chatUsers']
        users = CustomUser.objects.exclude(id__in=exclude_ids)
        serializer = UserListSerializer(users, many=True)
        return Response(
            {
                'usersToChat': serializer.data,
                "token": "Token is valid"
            },
            status=status.HTTP_200_OK
        )
        

class AccesToken(APIView):
    authentication_classes = [CustomTokenAuthentication]  
    permission_classes = [IsAuthenticated]

    # def post(self, request):
    #     data = request.auth
    #     user = request.user
    #     serializer = AccessTokenSerializer(user)
    #     return Response(
    #             {
    #                 'AccesToken': data,
    #                 "user": serializer.data
    #             },
    #             status=status.HTTP_200_OK
    #         )

    def post(self, request):
        access_token = request.auth
        userId = request.data['userId']
        user = get_object_or_404(CustomUser, id=userId)
        print('AccesToken ------------------------', request.auth)
        print('AccesToken userId ------------------------', userId)
        print('AccesToken user ------------------------', user)
        if user:                    
            # If the user exists, create a token
            user.token = f'{uuid4()}{uuid4()}{uuid4()}'
            user.access_token = access_token
            user.save()

            return Response(
                {
                    'message': 'Success',
                    'email': user.email,
                    'username': user.username,
                    'id': user.id,
                    'token': user.token,
                    'access_token': user.access_token,
                    'photo': f'/media/{user.photo}'
                }, 
                status=status.HTTP_200_OK
            )