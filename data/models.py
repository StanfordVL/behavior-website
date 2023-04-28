import numpy as np
from typing import List, Dict, Tuple
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
    def matching_task(self, task) -> Dict[str, Tuple[bool, str]]:
        ret = {readiness: {"matched": {}, "unmatched": {}} for readiness in ["ready", "not ready"]}
        for scene in self.all():
            for ready, ready_bool in zip(["ready", "not ready"], [True, False]):
                result = task.matching_scene(scene=scene, ready=ready_bool)
                if result[0] == matched:
                    ret[ready][scene.name] = result
        return ret




# Create your models here.    
class Scene(models.Model):
    objects = SceneManager()
    name = models.CharField(max_length=64, primary_key=True)

    def __str__(self):
        return self.name 
    


class Category(models.Model):
    name = models.CharField(max_length=64, primary_key=True)
    # the synset that the category belongs to
    synset = models.ForeignKey("Synset", on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.name
    
    def matching_synset(self, synset) -> bool:
        return self.synset.matching_synset(synset) if self.synset else False
        
    


class Object(models.Model):
    name = models.CharField(max_length=64, primary_key=True)
    # whether the object is in the current dataset
    ready = models.BooleanField(default=False)
    # whether the object is planned 
    planned = models.BooleanField(default=True)
    # the category that the object belongs to
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    # the photo of the object
    photo = models.ImageField("Object photo", blank=True, null=True)

    def __str__(self):
        return self.name
    
    def matching_synset(self, synset) -> bool:
        return self.category.matching_synset(synset)
    
    @property
    def state(self):
        if self.ready:
            return STATE_MATCHED 
        elif self.planned:
            return STATE_PLANNED
        return STATE_UNMATCHED
    


class Synset(models.Model):
    name = models.CharField(max_length=64, primary_key=True)
    # wordnet definitions
    definition = models.CharField(max_length=1000, default="")
    # whether the synset is legel (i.e. exists in the synset graph)
    legal = models.BooleanField(default=False)
    # whether the synset represents a substance
    is_substance = models.BooleanField(default=False)
    # all it's children in the synset graph
    children = models.ManyToManyField("self", blank=True, symmetrical=False, related_name="children_set")
    # all it's parent in the synset graph
    parents = models.ManyToManyField("self", blank=True, symmetrical=False, related_name="parents_set")

    def __str__(self):
        return self.name
    
    def matching_synset(self, synset_p) -> bool:
        """check whether this could match to synset_p (i.e. whether self is a child of synset_p)"""
        for synset_c in synset_p.children_set.all():
            if synset_c == self:
                return True
            elif self.matching_synset(synset_c):
                return True
        return False
    
    def get_all_parents(self):
        """get all parents of the synset"""
        parents = []
        for parent in self.parents_set.all():
            parents.append(parent)
            parents.extend(parent.get_parents())
        return parents

    @property
    def state(self):
        """overall state of the synset, one of STATE METADATA"""
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
        matched_objs = []
        for category in self.category_set.all():
            matched_objs.extend(category.object_set.all())
        for child in self.children_set.all():
            matched_objs.extend(child.matching_object)
        return matched_objs
    
    @property
    def matching_ready_object(self) -> List[Object]:
        """whether the synset is mapped to at least one object"""
        matched_ready_objs = []
        for category in self.category_set.all():
            matched_ready_objs.extend(category.object_set.filter(ready=True))
        for child in self.children_set.all():
            matched_ready_objs.extend(child.matching_ready_object)
        return matched_ready_objs
    
    @property
    def object_state(self) -> str:
        """Get the matching state of objects, returns STATE METADATA"""
        if not self.legal:
            return STATE_ILLEGAL
        else:
            if len(self.matching_ready_object) > 0:
                return STATE_MATCHED
            elif len(self.matching_object) > 0:
                return STATE_PLANNED
            else:
                return STATE_UNMATCHED
    
    @property
    def task_state(self):
        """Get whether the synset is required in any task, returns STATE METADATA"""
        return STATE_MATCHED if self.task_set.count() > 0 else STATE_NONE
    
    

class Task(models.Model):
    name = models.CharField(max_length=64, primary_key=True)
    # the synsets required by this task
    synsets = models.ManyToManyField(Synset)
    
    def __str__(self):
        return self.name
    
    def matching_scene(self, scene: Scene, ready: bool=True) -> Tuple[bool, str]:
        """checks whether a scene satisfies task requirements"""
        for room_requirement in self.roomrequirement_set.all():
            room_matched = False
            for room in scene.room_set.all():
                if room.matching_room_requirement(room_requirement, ready):
                    room_matched = True
                    break
            if not room_matched:
                return False, f"Cannot find suitable {room_requirement.type}"
        return True, ""
    
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
    def synset_state(self) -> str:
        if self.illegal_synsets.count() == 0:
            return STATE_UNMATCHED
        elif len(self.not_ready_synsets) > 0:
            return STATE_UNMATCHED
        elif len(self.ready_synsets) == 0:
            return STATE_PLANNED
        else:
            return STATE_MATCHED
    
    @property
    def matched_ready_scene(self):
        """scenes that are matched and ready"""
        return Scene.objects.matching_task(task=self, ready=True, matched=True)
    
    @property
    def matched_all_scene(self):
        """scenes that are matched"""
        return Scene.objects.matching_task(task=self, ready=False, matched=True)
    
    @property
    def unmatched_scene(self):
        """scenes that are unmatched"""
        return Scene.objects.matching_task(task=self, ready=False, matched=False)

    @property
    def scene_state(self) -> str:
        if len(self.matched_ready_scene) > 0:
            return STATE_MATCHED
        elif len(self.matched_all_scene) > 0:
            return STATE_PLANNED
        else:
            return STATE_UNMATCHED
        
    @property
    def substance_required(self) -> str:
        if self.substance_synsets.count() > 0:
            return STATE_SUBSTANCE
        else:
            return STATE_NONE



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
        for room_synset_requirement in room_requirement.roomsynsetrequirement_set.all():
            synset_name = room_synset_requirement.synset.name
            for i in range(room_synset_requirement.count):
                node_name = f"{synset_name}_{i}"
                G.add_node(node_name)
                synset_node_to_synset[node_name] = room_synset_requirement.synset
        # Add a node for each object in the room
        for roomobject in self.roomobject_set.all():
            for i in range(roomobject.count):
                object_name = f"{roomobject.object.name}_{i}"
                G.add_node(object_name)
                # Add edges to all matching synsets
                for synset_node, synset in synset_node_to_synset.items():
                    if roomobject.object.matching_synset(synset):
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