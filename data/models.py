import numpy as np
from typing import List, Dict
from django.db import models
from data.utils import *

ROOM_TYPE_CHOICES = [
    ('bar', 'bar'), 
    ('bathroom', 'bathroom'), 
    ('bedroom', 'bedroom'), 
    ('biology lab', 'biology_lab'), 
    ('break room', 'break_room'), 
    ('chemistry lab', 'chemistry_lab'),
    ('classroom', 'classroom'), 
    ('computer lab', 'computer_lab'), 
    ('conference hall', 'conference_hall'), 
    ('copy room', 'copy_room'), 
    ('corridor', 'corridor'), 
    ('dining room', 'dining_room'), 
    ('empty room', 'empty_room'), 
    ('grocery store', 'grocery_store'), 
    ('gym', 'gym'), 
    ('hammam', 'hammam'), 
    ('infirmary', 'infirmary'), 
    ('kitchen', 'kitchen'), 
    ('lobby', 'lobby'), 
    ('locker room', 'locker_room'), 
    ('meeting room', 'meeting_room'), 
    ('phone room', 'phone_room'), 
    ('private office', 'private_office'), 
    ('sauna', 'sauna'), 
    ('shared office', 'shared_office'), 
    ('spa', 'spa'), 
    ('entryway', 'entryway'), 
    ('television room', 'television_room'), 
    ('utility room', 'utility_room'), 
    ('garage', 'garage'), 
    ('closet', 'closet'), 
    ('childs room', 'childs_room'), 
    ('exercise room', 'exercise_room'), 
    ('garden', 'garden'), 
    ('living room', 'living_room'), 
    ('pantry room', 'pantry_room'), 
    ('playroom', 'playroom'), 
    ('staircase', 'staircase'), 
    ('storage room', 'storage_room')
]


class SceneManager(models.Manager):
    def matching_task(self, task, ready: bool) -> Dict[str, bool]:
        return {scene.name: task.matching_scene(scene=scene, ready=ready) for scene in self.all()}


# Create your models here.    
class Scene(models.Model):
    objects = SceneManager()
    name = models.CharField(max_length=64, primary_key=True)

    def __str__(self):
        return self.name 
    

class Category(models.Model):
    name = models.CharField(max_length=64, primary_key=True)
    # the synset that the category belongs to
    synset = models.ForeignKey("Synset", on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    
    def matching_synset(self, synset):
        return self.synset.maching_synset(synset)
    

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
    
    def matching_synset(self, synset):
        return self.category.matching_synset(synset)
    

class Synset(models.Model):
    name = models.CharField(max_length=64, primary_key=True)
    # wordnet definitions
    definition = models.CharField(max_length=1000, default="")
    # whether the synset is legel (i.e. exists in the synset graph)
    legal = models.BooleanField(default=False)
    # whether the synset represents a substance
    is_substance = models.BooleanField(default=False)
    # all it's children in the synset graph
    children = models.ManyToManyField("self", blank=True, symmetrical=False)
    # all it's parent in the synset graph
    parents = models.ManyToManyField("self", blank=True, symmetrical=False)

    def __str__(self):
        return self.name
    
    def matching_synset(self, synset_p) -> bool:
        """check whether this could match to synset_p (i.e. whether self is a child of synset_p)"""
        for synset_c in synset_p.children.all():
            if synset_c == self:
                return True
            elif self.maching_synset(synset_c):
                return True
        return False
    
    @property
    def state(self):
        """state of the synset, one of STATE METADATA"""
        if self.is_substance:
            return STATE_SUBSTANCE
        elif self.legal:
            if len(self.matching_ready_object) > 0:
                return STATE_MATCHED
            elif len(self.matching_object) > 0:
                return STATE_PLANNED
            else:
                return STATE_UNMATCHED
        else:
            return STATE_ILLEGAL
    
    @property
    def matching_object(self) -> List[Object]:
        return [obj for obj in Object.objects.all() if obj.matching_synset(self)]
    
    @property
    def matching_ready_object(self) -> List[Object]:
        """whether the synset is mapped to at least one object"""
        return [obj for obj in Object.objects.all() if obj.ready and obj.matching_synset(self)]

    

class Task(models.Model):
    name = models.CharField(max_length=64, primary_key=True)
    # the synsets required by this task
    synsets = models.ManyToManyField(Synset)
    
    def __str__(self):
        return self.name
    
    def matching_scene(self, scene: Scene, ready: bool=True) -> bool:
        """checks whether a scene satisfies task requirements"""
        for room_requirement in self.room_requirement_set.all():
            room_matched = False
            for room in scene.room_set.all():
                if room.matching_room_requirement(room_requirement, ready):
                    room_matched = True
                    break
            if not room_matched:
                return False
        return True
    
    @property
    def illegal_synsets(self):
        """synsets that are not legal (in the synset graph)"""
        return self.synsets.filter(legal=False).filter(is_substance=False)
    
    @property
    def substance_synsets(self):
        """synsets that represent a substance"""
        return self.synsets.filter(is_substance=True)
    
    @property
    def ready_synsets(self):
        """legal synsets that are mapped to at least one ready object"""
        return [synset for synset in self.synsets.filter(legal=True) if synset.matching_ready_object]
    
    @property
    def planned_synsets(self):
        """legal synsets that are mapped to at least one planned object"""
        return [synset for synset in self.synsets.filter(legal=True) if len(synset.matching_object) > 0]
    
    @property
    def not_ready_synsets(self):
        """legal synsets that are mapped to no object"""
        return [synset for synset in self.synsets.filter(legal=True) if len(synset.matching_object) == 0]
    
    @property
    def metadata(self) -> List[str]:
        synset_matching = METADATA_MATCHED if self.synsets.filter(legal=False).filter(is_substance=False).count() == 0 else METADATA_UNMATCHED
        if np.any(list(Scene.matching_task(task=self, ready=True).values())):
            scene_matching = METADATA_MATCHED
        elif np.any(list(Scene.matching_task(task=self, ready=False).values())):
            scene_matching = METADATA_PLANNED
        else:
            scene_matching = METADATA_UNMATCHED
        if np.all([len(Object.matching_synset(synset=synset, ready=True)) != 0 for synset in self.synsets.all()]):
            object_matching = METADATA_MATCHED
        elif np.all([len(Object.matching_synset(synset=synset, ready=False)) != 0 for synset in self.synsets.all()]):
            object_matching = METADATA_PLANNED
        else:
            object_matching = METADATA_UNMATCHED

        return [synset_matching, scene_matching, object_matching]


class RoomRequirement(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    type = models.CharField(max_length=64, choices=ROOM_TYPE_CHOICES)
    class Meta:
        unique_together = ('task', 'type')

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
    

class Room(models.Model):
    name = models.CharField(max_length=64)
    # type of the room
    type = models.CharField(max_length=64, choices=ROOM_TYPE_CHOICES)
    # whether the scene is ready in the current dataset
    ready = models.BooleanField(default=False)
    # the scene the room belongs to
    scene = models.ForeignKey(Scene, on_delete=models.CASCADE)
    class Meta:
        unique_together = ('name', 'ready', 'scene')
    
    def __str__(self):
        return f"{self.scene.name}_{self.type}_{'ready' if self.ready else 'planned'}" 

    def matching_room_requirement(self, room_requirement: RoomRequirement, ready: bool) -> bool:
        """checks whether the room satisfies the room requirement from a task"""
        if self.type != room_requirement.type or self.ready != ready: return False
        G = nx.Graph()
        # Add a node for each required object
        synset_node_to_synset = {}
        for room_synset_requirement in room_requirement.room_synset_requirement_set.all():
            synset_name = room_synset_requirement.synset.name
            for i in range(room_synset_requirement.count):
                node_name = f"{synset_name}_{i}"
                G.add_node(node_name)
                synset_node_to_synset[node_name] = room_synset_requirement.synset
        # Add a node for each object in the room
        for object in self.room_object_set.all():
            for i in range(object.count):
                object_name = f"{object.name}_{i}"
                G.add_node(object_name)
                # Add edges to all matching synsets
                for synset_node, synset in synset_node_to_synset.items():
                    if object.matching_synset(synset):
                        G.add_edge(object_name, synset_node)
        # Now do a bipartite matching
        M = nx.bipartite.maximum_matching(G, top_nodes=synset_node_to_synset.keys())
        # Now check that all required objects are matched
        return len(M) == len(synset_node_to_synset)


class RoomObject(models.Model):
    # the room that the object belongs to
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    # the actual object that the room object maps to
    object = models.ForeignKey(Object, on_delete=models.CASCADE)
    # number of objects in the room
    count = models.IntegerField()

    class Meta:
        unique_together = ('room', 'object')

    def __str__(self):
        return f"{str(self.room)}_{self.object.name}"   