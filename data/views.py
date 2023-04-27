from data.models import *
from django.shortcuts import render, get_object_or_404
from django.views.generic import DetailView, ListView


class TaskListView(ListView):
    model = Task
    context_object_name = "task_list"


class TaskDetailView(DetailView):
    model = Task
    context_object_name = "task"
        
    def get_queryset(self):
        self.task_name = get_object_or_404(Task, name=self.kwargs["task_name"])
        return Task.objects.filter(name=self.task_name)
    

class SynsetListView(ListView):
    model = Synset
    context_object_name = "synset_list"


class SynsetDetailView(DetailView):
    model = Synset
    context_object_name = "synset"

    def get_queryset(self):
        self.synset_name = get_object_or_404(Synset, name=self.kwargs["synset_name"])
        return Synset.objects.filter(name=self.synset_name)


class ObjectDetailView(DetailView):
    model = Object
    context_object_name = "object"

    def get_queryset(self):
        self.object_name = get_object_or_404(Object, name=self.kwargs["object_name"])
        return Object.objects.filter(name=self.object_name)   

    

# TODO: deprecated
def index(request):
    return render(request, "data/index.html", {})