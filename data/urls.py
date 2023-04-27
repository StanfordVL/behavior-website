from django.urls import path
from data.views import *

urlpatterns = [
    path("", views.index, name="index"),
    path("tasks/", TaskListView.as_view(), name="tasks list"),
    path("tasks/<str:task_name>", TaskDetailView.as_view(), name="task detail"),
    path("synsets/", SynsetListView.as_view(), name="synsets list"),
    path("synsets/<str:synset_name>", SynsetDetailView.as_view(), name="synset detail"),
]