from data.models import *
from django.shortcuts import render, get_object_or_404
from django.views.generic import DetailView, ListView


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

    

# TODO: deprecated
def index(request):
    return render(request, "data/index.html", {})