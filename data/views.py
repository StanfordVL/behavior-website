from data.models import *
from django.shortcuts import render, get_object_or_404
from django.views.generic import DetailView, ListView


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
    
    def get_queryset(self):
        return Task.objects.order_by("name")


class TaskDetailView(DetailView):
    model = Task
    context_object_name = "task"
    slug_field = "name"
    slug_url_kwarg = "task_name"

    def get_queryset(self):
        self.task = get_object_or_404(Task, name=self.kwargs["task_name"])
        return Task.objects.filter(name=self.kwargs["task_name"])
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add in the publisher
        context["scene_matching_dict"] = self.task.scene_matching_dict
        return context
    

class SynsetListView(ListView):
    model = Synset
    context_object_name = "synset_list"
    
    def get_queryset(self):
        return Synset.objects.order_by("name")
    

class SynsetDetailView(DetailView):
    model = Synset
    context_object_name = "synset"
    slug_field = "name"
    slug_url_kwarg = "synset_name"

    def get_queryset(self):
        self.synset_name = get_object_or_404(Synset, name=self.kwargs["synset_name"])
        return Synset.objects.filter(name=self.synset_name)
        

class ObjectDetailView(DetailView):
    model = Object
    context_object_name = "object"
    slug_field = "name"
    slug_url_kwarg = "object_name"

    def get_queryset(self):
        self.object_name = get_object_or_404(Object, name=self.kwargs["object_name"])
        return Object.objects.filter(name=self.object_name)   

    
def index(request):
    return render(request, "data/index.html", {})