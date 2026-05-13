from django.urls import path

from . import views


urlpatterns = [
    path("", views.todo_list, name="todo_list"),
    path("<int:pk>/open/", views.open_todo, name="todo_open"),
    path("<int:pk>/done/", views.complete_todo, name="todo_done"),
]
