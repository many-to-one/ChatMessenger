from django.contrib import admin
from .models import CustomUser, BlackListToken


class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        'username', 
        'email', 
        'login_at', 
        )


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(BlackListToken)
