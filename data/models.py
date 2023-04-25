import pathlib
from bddl.activity import Conditions
from django.db import models
from data.utils import *

# Create your models here.
class Scene(models.Model):
    name = models.CharField(max_length=30, primary_key=True)
    ready = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    

class Synset(models.Model):
    name = models.CharField(max_length=30, primary_key=True)
    is_substance = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    

class Task(models.Model):
    name = models.CharField(max_length=100, primary_key=True)
    synsets = models.ManyToManyField(Synset)
    scenes = models.ManyToManyField(Scene)
    
    def __str__(self):
        return self.name
    
    @classmethod
    def create(cls, task_fn):
        path = pathlib.Path(task_fn)
        task_file = path / "problem0.bddl"
        assert task_file.exists(), f"{name} file missing"
        name = path.name.replace(" ", "_").replace("-", "_").replace("'", "_")
        with open(task_file, "r") as f:
            predefined_problem = "".join(f.readlines())
        dom = "omnigibson" if "ObjectPropertyAnnotation" in str(task_file) else "igibson"
        conds = Conditions(name, "potato", dom, predefined_problem=predefined_problem)
        synsets = set(conds.parsed_objects.keys()) - {"agent.n.01"}
        raw_requirements = [cond[1:] for cond in conds.parsed_initial_conditions if cond[0] == "inroom"]
        assert all(len(req) == 2 for req in raw_requirements), f"{name}: {str(raw_requirements)} not in correct format"
        task_requirements[task_name] = sorted([(req.rsplit("_", 1)[0], rm) for req, rm in raw_requirements])
        task_to_scene_synset[task_name] = sorted([obj for obj, _ in task_requirements[task_name]])
        task_to_non_scene_synset[task_name] = sorted(task_to_synset[task_name] - set(task_to_scene_synset[task_name]))
        task_to_legal_synsets[task_name] = sorted(task_to_synset[task_name] & legit_synsets)
        task_to_illegal_synsets[task_name] = sorted(task_to_synset[task_name] - set(task_to_legal_synsets[task_name]))
        # get task scene mapping
        all_task_to_scene, cur_task_to_scene = {}, {}
        for task_to_scene, scenes in zip([all_task_to_scene, cur_task_to_scene], [all_scenes, cur_scenes]):
            for task_name in task_to_fn:
                task_to_scene[task_name] = {"matched": [], "unmatched": {}}
                for scene in scenes:
                    ret = scene_compatible_with_task(G, scenes, scene, task_requirements[task_name]) 
                    if len(ret) == 0:
                        task_to_scene[task_name]["matched"].append(scene)
                    else:
                        task_to_scene[task_name]["unmatched"][scene] = ret
        task = cls(name=name, synsets=synsets, )

        return task


class Category(models.Model):
    name = models.CharField(max_length=30, primary_key=True)
    is_substance = models.BooleanField(default=False)
    synset = models.ForeignKey(Synset, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    
    @classmethod
    def create(cls, name: str, synset_name: str):
        # always set substance to false initially
        synset = Synset.objects.get_or_create(name=synset_name, is_substance=False)
        synset.save()
        category = cls(name=name, is_substance=False, synset=synset)
        return category


class Object(models.Model):
    name = models.CharField(max_length=30, primary_key=True)
    ready = models.BooleanField(default=False)
    is_substance = models.BooleanField(default=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    synset = models.ForeignKey(Synset, on_delete=models.CASCADE)
    tasks = models.ManyToManyField(Task)

    def __str__(self):
        return self.name
    
    @classmethod
    def create(cls, name: str, ready: bool):
        category_name = name.split("-")[0]
        category = Synset.objects.get_or_create(name=category_name)
        object = cls(name=name, ready=ready, category=category)
        return object

