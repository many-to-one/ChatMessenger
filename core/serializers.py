from rest_framework import serializers
from .models import Message, Chat, Conversation
from users.models import CustomUser

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = (
            'id', 
            'username', 
            'incomingFriendRequest',
            'acceptFriendRequest',
            'outComingFriendRequest',
            'photo'
            )
        
class FriendListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = (
            'id', 
            'username', 
            'photo',
            )

class MessageSerializer(serializers.ModelSerializer):

    class Meta:
        model = Message
        fields = '__all__'


class ChatSerializer(serializers.ModelSerializer):

    class Meta:
        model = Chat
        fields = '__all__'


class ConversationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Conversation
        fields = '__all__'