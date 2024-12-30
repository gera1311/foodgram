from django.contrib import admin

from .models import User, Follow


class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name', 'username', 'avatar']
    search_fields = ['first_name', 'email']
    ordering = ['username']


class FollowAdmin(admin.ModelAdmin):
    model = Follow


admin.site.register(User, UserAdmin)
admin.site.register(Follow, FollowAdmin)
