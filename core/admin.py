from django.contrib import admin
from .models import *
from users.models import FriendList

admin.site.register(Message)
admin.site.register(Chat)
admin.site.register(Conversation)
admin.site.register(FriendList)
admin.site.register(IncomingFriendRequest)
admin.site.register(OutcomingFriendRequest)
admin.site.register(BlockedUsers)
