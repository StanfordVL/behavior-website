from data.models import *
from django.shortcuts import render


def index(request):
    return render(request, "data/index.html", {})

def tasks_list(request):
    tasks = Task.objects.all()
    return render(request, "data/tasks_list.html", {"tasks": tasks})

def task(request, task_name):
    task = Task.objects.get(task_name)
    return render(request, "data/task.html", {"task": task})

def synsets(request):
    return render(request, "data/synsets.html", {})