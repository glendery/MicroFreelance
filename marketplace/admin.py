from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Project

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role', 'balance')}),
    )
    list_display = ['username', 'email', 'role', 'balance', 'is_staff']

admin.site.register(User, CustomUserAdmin)
admin.site.register(Project)
