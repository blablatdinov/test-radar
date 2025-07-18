from django.contrib import admin

from auth.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    search_fields = ['username']
