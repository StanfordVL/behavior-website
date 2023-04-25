import pathlib
from bddl.activity import Conditions
from django.db import models
from data.utils import *

# Create your models here.    
class Scene(models.Model):
    name = models.CharField(max_length=30)
    # whether the scene is ready in the current dataset
    ready = models.BooleanField(default=False)
    # the room config dict (serialized) containing its room and object configurations
    room_config = models.CharField(max_length=1000)
    class Meta:
        unique_together = ('name', 'ready')

    def __str__(self):
        return self.name 
    

class Synset(models.Model):
    name = models.CharField(max_length=30, primary_key=True)
    # whether the synset represents a substance
    is_substance = models.BooleanField(default=False)
    # whether the synset is present in the synset graph G
    legal = models.BooleanField(default=False)
    # all it's children in the synset graph
    children = models.ManyToManyField("Synset", blank=True, symmetrical=False)

    def __str__(self):
        return self.name
        

class Task(models.Model):
    name = models.CharField(max_length=30, primary_key=True)
    # room requirements for the task
    room_requirements = models.CharField(max_length=300)
    # the synsets required by this task
    synsets = models.ManyToManyField(Synset)
    
    def __str__(self):
        return self.name
    
    def get_scene_matching(self, G, scene: Scene):
        return scene_compatible_with_task(G, scene, self.room_requirements)

class Category(models.Model):
    name = models.CharField(max_length=30, primary_key=True)
    # the synset that the category belongs to
    synset = models.ForeignKey(Synset, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Object(models.Model):
    name = models.CharField(max_length=30, primary_key=True)
    # whether the object is in the current dataset
    ready = models.BooleanField(default=False)
    # the category that the object belongs to
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

