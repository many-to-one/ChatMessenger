from django.urls import path
from .views import *
from django.contrib import admin

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('users/', UserListView.as_view(), name='users'),
    path('accessToken/', AccesToken.as_view(), name='accessToken'),
]