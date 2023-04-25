from django.shortcuts import render

from data.models import Task

# 1. create scenes
# 2. create categories and synsets (with category_mappings.csv)
# 2. create objects and map to categories (with object inventory)
# 3. create synsets and map to synsets and scenes(with bddl)

def index(request):
    return render(request, "data/index.html", {})

def tasks_list(request):
    return render(request, "data/index.html", {})

def synsets(request):
    return render(request, "data/index.html", {})