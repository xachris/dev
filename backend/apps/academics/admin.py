from django.contrib import admin

from .models import ClassGroup, HomeroomAssignment, StudentClassMembership, Subject, TeachingAssignment


@admin.register(ClassGroup)
class ClassGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "group_type", "academic_year")
    list_filter = ("group_type", "academic_year__school", "academic_year")
    search_fields = ("name", "academic_year__name", "academic_year__school__name")


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "school")
    list_filter = ("school",)
    search_fields = ("code", "name", "school__name")


@admin.register(StudentClassMembership)
class StudentClassMembershipAdmin(admin.ModelAdmin):
    list_display = ("student_membership", "class_group", "is_active")
    list_filter = ("is_active", "class_group__group_type", "class_group__academic_year__school")
    search_fields = (
        "student_membership__student__full_name",
        "student_membership__student_number",
        "class_group__name",
    )


@admin.register(TeachingAssignment)
class TeachingAssignmentAdmin(admin.ModelAdmin):
    list_display = ("teacher_role", "subject", "class_group", "is_active")
    list_filter = ("is_active", "subject__school", "class_group__group_type")
    search_fields = (
        "teacher_role__user__display_name",
        "teacher_role__user__username",
        "subject__code",
        "subject__name",
        "class_group__name",
    )


@admin.register(HomeroomAssignment)
class HomeroomAssignmentAdmin(admin.ModelAdmin):
    list_display = ("teacher_role", "class_group", "is_active")
    list_filter = ("is_active", "class_group__academic_year__school")
    search_fields = (
        "teacher_role__user__display_name",
        "teacher_role__user__username",
        "class_group__name",
    )
