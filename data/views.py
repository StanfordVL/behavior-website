from data.models import *
from typing import Any
from django.shortcuts import render, get_object_or_404
from django.views.generic import DetailView, ListView


class TaskListView(ListView):
    model = Task
    context_object_name = "task_list"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        return context


class TaskDetailView(DetailView):
    model = Task
    context_object_name = "task"
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        return context
    
    def get_queryset(self):
        self.task_name = get_object_or_404(Task, name=self.kwargs["task_name"])
        return Task.objects.filter(name=self.task_name)
    

class SynsetListView(ListView):
    model = Synset
    context_object_name = "synset_list"


class SynsetDetailView(DetailView):
    model = Synset
    context_object_name = "synset"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        return context
    


# deprecated
def index(request):
    return render(request, "data/index.html", {})

def tasks_list(request):
    tasks_metadata = Task.objects.metadata
    return render(request, "data/tasks_list.html", {"tasks_metadata": tasks_metadata})

def task(request, task_name):
    task = Task.objects.get(task_name)
    return render(request, "data/task.html", {"task": task})

def synsets(request):
    synsets_data = {}
    for synset in Synset.objects.all():
        tasks = sorted([task.name for task in synset.task_set.all()])
        objects_ready = Object.objects.matching_synset(synset, ready=True)
        objects_planned = Object.objects.matching_synset(synset, ready=False)
        synsets_data[synset.name] = [tasks, objects_ready, objects_planned]
    return render(request, "data/synsets_list.html", {"synsets_data": synsets_data})