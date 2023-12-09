from django.contrib import admin
from .models import *

admin.site.register(Message)
admin.site.register(Chat)
admin.site.register(Conversation)
admin.site.register(IncomingFriendRequest)
admin.site.register(OutcomingFriendRequest)
admin.site.register(BlockedUsers)
admin.site.register(OnPage)
