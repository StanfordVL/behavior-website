from django.contrib.sitemaps.views import sitemap
from django.urls import path
from data.views import *

urlpatterns = [
    path("", index, name="index"),
    path("tasks/", TaskListView.as_view(), name="tasks list"),
    path("synsets/", SynsetListView.as_view(), name="synsets list"),
    path("tasks/<task_name>", TaskDetailView.as_view(), name="task detail"),
    path("synsets/<synset_name>", SynsetDetailView.as_view(), name="synset detail"),
    path("objects/<object_name>", ObjectDetailView.as_view(), name="object detail"),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": {}},
        name="django.contrib.sitemaps.views.sitemap",
    )
]