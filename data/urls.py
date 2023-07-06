from django.contrib.sitemaps.views import sitemap
from django.urls import path
from data.views import *

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("tasks/", TaskListView.as_view(), name="task_list"),
    path("nonscenematchedtasks/", NonSceneMatchedTaskListView.as_view(), name="non-scene-matched_task_list"),
    path("b20tasks/", B20TaskListView.as_view(), name="b20_task_list"),
    path("objects/", ObjectListView.as_view(), name="object_list"),
    path("substancemappedobjects/", SubstanceMappedObjectListView.as_view(), name="substance_mapped_object_list"),
    path("scenes/", SceneListView.as_view(), name="scene_list"),
    path("synsets/", SynsetListView.as_view(), name="synset_list"),
    path("categories/", CategoryListView.as_view(), name="category_list"),
    path("misspelledcategories/", MisspelledCategoryListView.as_view(), name="misspelled_category_list"),
    path("nonleafsynsets/", NonLeafSynsetListView.as_view(), name="non-leaf_synset_list"),
    path("substanceerrorsynsets/", SubstanceErrorSynsetListView.as_view(), name="substance_error_synset_list"),
    path("misspelledsynsets/", MisspelledSynsetListView.as_view(), name="misspelled_synset_list"),
    path("fillablesynsets/", FillableSynsetListView.as_view(), name="fillable_synset_list"),
    path("unsupportedpropertysynsets/", UnsupportedPropertySynsetListView.as_view(), name="unsupported_property_synset_list"),
    path("tasks/<task_name>/", TaskDetailView.as_view(), name="task_detail"),
    path("synsets/<synset_name>/", SynsetDetailView.as_view(), name="synset_detail"),
    path("categories/<category_name>/", CategoryDetailView.as_view(), name="category_detail"),
    path("scenes/<scene_name>/", SceneDetailView.as_view(), name="scene_detail"),
    path("objects/<object_name>/", ObjectDetailView.as_view(), name="object_detail"),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": {}},
        name="django.contrib.sitemaps.views.sitemap",
    )
]