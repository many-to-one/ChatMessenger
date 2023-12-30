from django.db import models
from users.models import CustomUser

class Message(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    resend = models.BooleanField(default=False)
    unread = models.BooleanField(default=True)
    chat = models.ForeignKey(
        'Chat', 
        on_delete=models.CASCADE, 
        null=True
        )
    conversation = models.ForeignKey(
        'Conversation', 
        on_delete=models.CASCADE, 
        null=True
        )

    def __str__(self):
        return self.content
    
    def user_photo(self):
        return f'/media/{self.user.photo}' if self.user.photo else None,
    

class Chat(models.Model):
    name = models.CharField(
        null=True,
        max_length=50
    )
    user = models.ManyToManyField(CustomUser)
    timestamp = models.DateTimeField(auto_now_add=True)
    creater = models.CharField(
        null=True,
        max_length=50
    )
    def __str__(self):
        return self.name
    
    def usernames(self):
        return [user.username for user in self.user.all()]

    def user_info(self):
        user_data = []
        for user in self.user.all():
            user_info = {
                'id': user.id,
                'username': user.username,
                'photo': f'/media/{user.photo}' if user.photo else None,
                'creater': self.creater
            }
            user_data.append(user_info)
        return user_data
    

class Conversation(models.Model):
    user = models.ManyToManyField(CustomUser)

    def __str__(self):
        return str(self.id)
    

class OnPage(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        null=True,
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        null=True,
    )
    

class OutcomingFriendRequest(models.Model):
    user = models.ForeignKey(
        CustomUser, 
        null=True,
        on_delete=models.CASCADE, 
        related_name='sender',
        )
    outUsers = models.ManyToManyField(
        CustomUser, 
        related_name='receivers'
        )

    
    def __str__(self):
        return str(self.user)
    

class IncomingFriendRequest(models.Model):
    user = models.ForeignKey(
        CustomUser, 
        null=True,
        on_delete=models.CASCADE, 
        related_name='receiver',
        )
    inUsers = models.ManyToManyField(
        CustomUser, 
        related_name='senders'
        )

    
    def __str__(self):
       return str(self.user)
    

class BlockedUsers(models.Model):
    user = models.ForeignKey(
        CustomUser, 
        null=True,
        on_delete=models.CASCADE, 
        related_name='blockingUser',
        )
    blockedUsers = models.ManyToManyField(
        CustomUser, 
        related_name='blockedUsers'
        )

    
    def __str__(self):
        return str(self.user)