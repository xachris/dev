from django.contrib import admin

from .models import AcademicYear, School


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "status", "language_code", "timezone")
    list_filter = ("status", "language_code", "timezone")
    search_fields = ("name", "code")


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ("name", "school", "starts_on", "ends_on", "is_active")
    list_filter = ("school", "is_active")
    search_fields = ("name", "school__name", "school__code")
