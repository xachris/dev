from django.contrib.auth import views as auth_views
from django.urls import path

from . import pilot_views, views

app_name = "core"

urlpatterns = [
    path("", pilot_views.home, name="home"),
    path("health/", views.health, name="health"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="core:home"),
        name="logout",
    ),
    path("dashboard/", pilot_views.dashboard, name="dashboard"),
    path(
        "teacher/comment/<uuid:comment_id>/",
        pilot_views.teacher_comment,
        name="teacher_comment",
    ),
    path(
        "homeroom/report/<uuid:report_id>/",
        pilot_views.homeroom_report,
        name="homeroom_report",
    ),
    path(
        "publish/report/<uuid:report_id>/",
        pilot_views.publish_report_view,
        name="publish_report",
    ),
    path(
        "report/<uuid:report_id>/",
        pilot_views.report_view,
        name="report_view",
    ),
    path("demo/reset/", pilot_views.demo_reset, name="demo_reset"),
]
