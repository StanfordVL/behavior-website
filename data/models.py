import csv

from django.db import models
from data.utils import *

# get allowed room types from the csv file
with open(f'{os.path.pardir}/ig_pipeline/metadata/allowed_room_types.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    room_types = [(row[0].replace('_', ' '), row[0]) for row in reader][1:]


# Create your models here.    
class Scene(models.Model):
    name = models.CharField(max_length=64, primary_key=True)

    def __str__(self):
        return self.name 


class Synset(models.Model):
    name = models.CharField(max_length=64, primary_key=True)
    # wordnet definitions
    definition = models.CharField(max_length=1000)
    # whether the synset represents a substance
    is_substance = models.BooleanField(default=False)
    # whether the synset is present in the synset graph G
    legal = models.BooleanField(default=False)
    # all it's children in the synset graph
    children = models.ManyToManyField("self", blank=True, symmetrical=False)

    def __str__(self):
        return self.name
        

class Task(models.Model):
    name = models.CharField(max_length=64, primary_key=True)
    # room requirements for the task
    room_requirements = models.CharField(max_length=300)
    # the synsets required by this task
    synsets = models.ManyToManyField(Synset)
    
    def __str__(self):
        return self.name
    
    def get_scene_matching(self, G, scene: Scene):
        return scene_compatible_with_task(G, scene.room_config, self.room_requirements)


class Category(models.Model):
    name = models.CharField(max_length=64, primary_key=True)
    # the synset that the category belongs to
    synset = models.ForeignKey(Synset, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Object(models.Model):
    name = models.CharField(max_length=64, primary_key=True)
    # whether the object is in the current dataset
    ready = models.BooleanField(default=False)
    # the category that the object belongs to
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    # the photo of the object
    photo = models.ImageField("Object photo", blank=True)

    def __str__(self):
        return self.name


class Room(models.Model):
    name = models.CharField(max_length=64)
    # type of the room
    type = models.CharField(max_length=64, choices=room_types)
    # whether the scene is ready in the current dataset
    ready = models.BooleanField(default=False)
    # the scene the room belongs to
    scene = models.ForeignKey(Scene, on_delete=models.CASCADE)
    class Meta:
        unique_together = ('name', 'type', 'ready', 'scene')
    
    def __str__(self):
        return f"{self.scene.name}_{self.type}_{'ready' if self.ready else 'planned'}" 
    

class RoomObject(models.Model):
    # the room that the object belongs to
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    # the actual object that the room object maps to
    object = models.ForeignKey(Object, on_delete=models.CASCADE)
    # number of objects in the room
    count = models.IntegerField()

    class Meta:
        unique_together = ('room', 'object', 'count')

    def __str__(self):
        return f"{str(self.room)}_{self.object.name}" 
    

class RoomRequirement(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    room_type = models.CharField(max_length=64, choices=room_types)
    class Meta:
        unique_together = ('task', 'room_type')

    def __str__(self):
        return f"{self.task.name}_{self.room_type}" 


class RoomSynsetRequirement(models.Model):
    room_requirement = models.ForeignKey(RoomRequirement, on_delete=models.CASCADE)
    synset = models.ForeignKey(Synset, on_delete=models.CASCADE)
    count = models.IntegerField()

    class Meta:
        unique_together = ('room_requirement', 'synset')

    def __str__(self):
        return f"{str(self.room_requirement)}_{self.synset.name}" 
  