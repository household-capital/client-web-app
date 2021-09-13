from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Profile, Referer, SessionLog

class ProfileInline(admin.StackedInline):
    """Inline model definitions"""
    model = Profile
    can_delete = False
    verbose_name_plural = 'profile'

class UserAdmin(BaseUserAdmin):
    """Set profile model as an in-line user model within admin"""
    inlines = (ProfileInline,)

class SessionLogAdmin(admin.ModelAdmin):
    """Admin view settings """

    list_display = ('description', 'timestamp', 'referenceUID')
    ordering = ('-timestamp',)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Referer)
admin.site.register(SessionLog, SessionLogAdmin)
