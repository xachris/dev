from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import RoleAssignment, UserAccount


@admin.register(UserAccount)
class UserAccountAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("平台信息", {"fields": ("display_name",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("平台信息", {"fields": ("display_name",)}),)
    list_display = ("username", "display_name", "email", "is_active", "is_staff")
    search_fields = ("username", "display_name", "email")


@admin.register(RoleAssignment)
class RoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ("user", "school", "role", "is_active", "updated_at")
    list_filter = ("school", "role", "is_active")
    search_fields = ("user__username", "user__display_name", "school__name", "school__code")
