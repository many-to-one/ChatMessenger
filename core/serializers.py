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
        

class ConversationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Conversation
        fields = '__all__'


class Conv(serializers.ModelSerializer):

    class Meta:
        model = Conversation
        fields = (
            'id',
        )


class MessageSerializer(serializers.ModelSerializer):
    # user = serializers.PrimaryKeyRelatedField(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(source='user', read_only=True)
    # conversation_id = ConversationSerializer()
    conversation_id = serializers.PrimaryKeyRelatedField(source='conversation', read_only=True)
    chat_id = serializers.PrimaryKeyRelatedField(source='chat', read_only=True)
    timestamp = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = Message
        fields = '__all__'


class ChatSerializer(serializers.ModelSerializer):
    # user_id = serializers.PrimaryKeyRelatedField(source='user', read_only=True)

    class Meta:
        model = Chat
        fields = '__all__'