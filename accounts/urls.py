from django.urls import path

from . import views


urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("manage/members/", views.manage_members, name="manage_members"),
    path("manage/logs/", views.manage_logs, name="manage_logs"),
]
