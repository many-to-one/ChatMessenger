from django.urls import path

from .views import *

urlpatterns = [
    path('', MessageList.as_view(), name='MessageList'),
    path('createChat/', CreateChatRoom.as_view(), name='createChat'),
    path('allMessages/<chat_id>/', AllUserRoomMessages.as_view(), name='allMessages'),
    path('allChats/<user_id>/', AllChatRooms.as_view(), name='allChats'),
    path('deleteChat/<chat_id>/', DeleteChatRoom.as_view(), name='deleteChat'),
    path('conversations/', ConversationRoom.as_view(), name='conversations'),
    path('getConversation/<conv_id>/', GetConversationView.as_view(), name='conversations'),
    path('saveMess/', SaveMessage.as_view(), name='saveMess'),
    path('delUser/', DeleteUser.as_view(), name='delUser'),
]