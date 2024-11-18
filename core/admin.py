from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from core.models import CustomUser, Subscription

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'bio')
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('bio', )}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('username', 'bio')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Subscription)
