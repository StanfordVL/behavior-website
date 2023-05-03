from django.contrib.sitemaps.views import sitemap
from django.urls import path
from data.views import *

urlpatterns = [
    path("", index, name="index"),
    path("tasks/", TaskListView.as_view(), name="task_list"),
    path("objects/", ObjectListView.as_view(), name="object_list"),
    path("scenes/", SceneListView.as_view(), name="scene_list"),
    path("synsets/", SynsetListView.as_view(), name="synset_list"),
    path("nonleafsynsets/", NonLeafSynsetListView.as_view(), name="non-leaf_synset_list"),
    path("tasks/<task_name>", TaskDetailView.as_view(), name="task_detail"),
    path("synsets/<synset_name>", SynsetDetailView.as_view(), name="synset_detail"),
    path("scenes/<scene_name>", SceneDetailView.as_view(), name="scene_detail"),
    path("objects/<object_name>", ObjectDetailView.as_view(), name="object_detail"),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": {}},
        name="django.contrib.sitemaps.views.sitemap",
    )
]