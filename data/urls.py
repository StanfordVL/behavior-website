from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("tasks/", views.tasks_list, name="tasks list"),
    path("tasks/<str:task_name>", views.task, name="task detail"),
    path("synsets/", views.synsets, name="synsets"),
]