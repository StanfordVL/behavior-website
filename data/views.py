from typing import List
from data.models import *
from data.utils import *
from django.db.models import Count
from django.views.generic import DetailView, ListView, TemplateView


B20 = {
    "attach_a_camera_to_a_tripod",
    "boil_water",
    "chop_an_onion",
    "clean_up_broken_glass",
    "cleaning_bathtub",
    "fill_a_bucket_in_a_small_sink",
    "folding_piece_of_cloth",
    "freeze_pies",
    "hanging_up_bedsheets",
    "make_a_steak",
    "make_a_strawberry_slushie",
    "melt_white_chocolate",
    "mixing_drinks",
    "mowing_the_lawn",
    "putting_away_Halloween_decorations",
    "putting_away_toys",
    "putting_up_shelves",
    "setting_the_fire",
    "spraying_for_bugs",
    "thawing_frozen_food",
}


class TaskListView(ListView):
    model = Task
    context_object_name = "task_list"


class B20TaskListView(TaskListView):
    queryset = Task.objects.order_by("name").filter(name__in=B20)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "B-20 Tasks"
        return context
    

class NonSceneMatchedTaskListView(TaskListView):
    template_name = "data/task_list.html"

    def get_queryset(self) -> List[Task]:
        return [x for x in super().get_queryset().all() if x.scene_state == STATE_UNMATCHED]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Non-Scene-Matched Tasks"
        return context


class ObjectListView(ListView):
    model = Object
    context_object_name = "object_list"


class SceneListView(ListView):
    model = Scene
    context_object_name = "scene_list"


class SynsetListView(ListView):
    model = Synset
    context_object_name = "synset_list"
    

class NonLeafSynsetListView(SynsetListView):
    queryset = (Synset.objects
                .annotate(
                    num_objects=Count('category__object'),
                    num_child_synsets=Count('children'))
                .filter(num_objects__gt=0, num_child_synsets__gt=0)
                .order_by("name"))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Non-Leaf Object-Assigned Synsets"
        return context


class TaskDetailView(DetailView):
    model = Task
    context_object_name = "task"
    slug_field = "name"
    slug_url_kwarg = "task_name"
    

class SynsetDetailView(DetailView):
    model = Synset
    context_object_name = "synset"
    slug_field = "name"
    slug_url_kwarg = "synset_name"
        

class ObjectDetailView(DetailView):
    model = Object
    context_object_name = "object"
    slug_field = "name"
    slug_url_kwarg = "object_name" 
    

class SceneDetailView(DetailView):
    model = Scene
    context_object_name = "scene"
    slug_field = "name"
    slug_url_kwarg = "scene_name"


class IndexView(TemplateView):
    template_name = "data/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # task metadata
        tasks_state = [task.state for task in Task.objects.all()]
        context["task_metadata"] = [
            len([state for state in tasks_state if state == STATE_MATCHED]),
            len([state for state in tasks_state if state == STATE_PLANNED]),
            len([state for state in tasks_state if state == STATE_UNMATCHED]),
            len(tasks_state)
        ]
        # sysnet metadata
        context["synset_metadata"] = [
            Synset.objects.filter(state=STATE_MATCHED).count(), 
            Synset.objects.filter(state=STATE_PLANNED).count(),
            Synset.objects.filter(state=STATE_SUBSTANCE).count(),
            Synset.objects.filter(state=STATE_UNMATCHED).count(),
            Synset.objects.filter(state=STATE_ILLEGAL).count(),
            Synset.objects.count(),
        ]
        # object metadata
        context["object_metadata"] = [
            Object.objects.filter(ready=True).count(), 
            Object.objects.filter(ready=False, planned=True).count(),
            Object.objects.filter(planned=False).count(),
        ]
        # scene metadata
        num_ready_scenes = sum([scene.any_ready for scene in Scene.objects.all()])
        num_planned_scenes = Scene.objects.count() - num_ready_scenes
        context["scene_metadata"] = [num_ready_scenes, num_planned_scenes]
        return context
    
