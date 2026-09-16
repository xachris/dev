from django.contrib import admin

from .models import GuardianRelationship, Student, StudentSchoolMembership


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("full_name", "id", "user_account", "updated_at")
    search_fields = ("full_name", "user_account__username", "user_account__display_name")


@admin.register(StudentSchoolMembership)
class StudentSchoolMembershipAdmin(admin.ModelAdmin):
    list_display = ("student_number", "student", "school", "status", "updated_at")
    list_filter = ("school", "status")
    search_fields = ("student_number", "student__full_name", "school__name", "school__code")


@admin.register(GuardianRelationship)
class GuardianRelationshipAdmin(admin.ModelAdmin):
    list_display = ("guardian", "student_membership", "relationship_type", "is_active")
    list_filter = ("relationship_type", "is_active", "student_membership__school")
    search_fields = (
        "guardian__username",
        "guardian__display_name",
        "student_membership__student__full_name",
        "student_membership__student_number",
    )
