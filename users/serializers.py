from rest_framework import serializers
from .models import CustomUser

class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'})

    class Meta:
        model = CustomUser
        fields = [
            'username',
            'email',
            'password'
        ]
    

class LoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'})

    class Meta:
        model = CustomUser
        fields = [
            'email',
            'password',
            'login_at',
        ]


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id',
            'username',
            'email',
            'photo',
        ]

    
class AccessTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id',
            'username',
            'email',
            'photo',
            'token',
            'access_token',
        ]