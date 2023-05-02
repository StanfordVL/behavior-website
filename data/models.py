from django.db.models.query import QuerySet
import networkx as nx
from django.utils.functional import cached_property
from typing import Dict, Set
from django.db import models
from data.utils import *
from collections import defaultdict

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


class Scene(models.Model):
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
        return synset.name in self.matching_synsets

    @cached_property
    def matching_synsets(self) -> Set["Synset"]:
        return set(self.synset.ancestors.values_list("name", flat=True)) if self.synset else set()


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
    
    @cached_property
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
    # all it's parents in the synset graph (NOTE: this does not include self)
    parents = models.ManyToManyField("self", blank=True, symmetrical=False, related_name="children")
    # all ancestors (NOTE: this include self)
    ancestors = models.ManyToManyField("self", blank=True, symmetrical=False, related_name="descendants")
    # state of the synset, one of STATE METADATA (pre computed to save webpage generation time)
    state = models.CharField(max_length=64, default=STATE_NONE)

    def __str__(self):
        return self.name
    
    @cached_property
    def matching_object(self) -> Set[Object]:
        matched_objs = set()
        for synset in self.descendants.all():
            for category in synset.category_set.all():
                matched_objs.update(category.object_set.all())
        return matched_objs
    
    @cached_property
    def matching_ready_object(self) -> Set[Object]:
        """whether the synset is mapped to at least one object"""
        matched_ready_objs = set()
        for synset in self.descendants.all():
            for category in synset.category_set.all():
                matched_ready_objs.update(category.object_set.filter(ready=True))
        return matched_ready_objs
    
    @cached_property
    def task_state(self):
        """Get whether the synset is required in any task, returns STATE METADATA"""
        return STATE_MATCHED if self.task_set.count() > 0 else STATE_NONE
    

class TaskManager(models.Manager):
    def get_queryset(self) -> QuerySet:
        return super().get_queryset().prefetch_related(
            "synsets",
            "roomrequirement_set__roomsynsetrequirement_set__synset"
        )
            

class Task(models.Model):
    objects = TaskManager()
    name = models.CharField(max_length=64, primary_key=True)
    # the synsets required by this task
    synsets = models.ManyToManyField(Synset)
    
    def __str__(self):
        return self.name
    
    def matching_scene(self, scene: Scene, ready: bool=True) -> str:
        """checks whether a scene satisfies task requirements"""
        ret = ""
        for room_requirement in self.roomrequirement_set.all():
            scene_ret = f"Cannot find suitable {room_requirement.type}: "
            for room in scene.room_set.all():
                if room.type != room_requirement.type or room.ready != ready:
                    continue
                room_ret = room.matching_room_requirement(room_requirement)
                if len(room_ret)== 0:
                    scene_ret = ""
                    break
                else: 
                    scene_ret += f"{room.name} is missing {room_ret}; "
            if len(scene_ret) > 0:
                ret += scene_ret[:-2] + "."
        return ret
    
    @cached_property
    def illegal_synsets(self):
        """synsets that are not legal (in the synset graph)"""
        return self.synsets.filter(legal=False, is_substance=False)
    
    @cached_property
    def substance_synsets(self):
        """synsets that represent a substance"""
        return self.synsets.filter(is_substance=True)
    
    @cached_property
    def synset_state(self) -> str:
        if self.illegal_synsets.count() > 0:
            return STATE_UNMATCHED
        elif self.synsets.filter(state=STATE_UNMATCHED).count() > 0:
            return STATE_UNMATCHED
        elif self.synsets.filter(state=STATE_MATCHED).count() == 0:
            return STATE_PLANNED
        else:
            return STATE_MATCHED
        
    @cached_property
    def problem_synsets(self):
        return self.illegal_synsets | self.synsets.filter(state=STATE_UNMATCHED)
    
    @cached_property
    def scene_matching_dict(self) -> Dict[str, Dict[str, str]]:
        ret = {status: {} for status in ["matched", "planned", "unmatched"]}
        for scene in Scene.objects.prefetch_related("room_set__roomobject_set__object__category__synset").all():
            # first check whether it can be matched to the task in the future
            result = self.matching_scene(scene=scene, ready=False)
            # if it is matched, check whether it can be matched to the task it its current state
            if len(result) == 0:
                result_cur = self.matching_scene(scene=scene, ready=True)
                if len(result_cur) == 0:
                    ret["matched"][scene.name] = result_cur
                else:
                    ret["planned"][scene.name] = result_cur # store why it can't be matched currently
            else:
                ret["unmatched"][scene.name] = result
        return ret
    
    @cached_property
    def scene_state(self) -> str:
        scene_matching_dict = self.scene_matching_dict
        if len(scene_matching_dict["matched"]) > 0:
            return STATE_MATCHED
        elif len(scene_matching_dict["planned"]) > 0:
            return STATE_PLANNED
        else:
            return STATE_UNMATCHED
        
    @cached_property
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

    def matching_room_requirement(self, room_requirement: RoomRequirement) -> str:
        """
        checks whether the room satisfies the room requirement from a task
        returns an empty string if it does, otherwise returns a string describing what is missing
        """
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
        if len(M) == len(synset_node_to_synset):
            return ""
        else: 
            missing_synsets = defaultdict(int)  # default value is 0
            for synset_node, synset in synset_node_to_synset.items():
                if synset_node not in M:
                    missing_synsets[synset.name] += 1
            return ", ".join([f"{count} {synset}" for synset, count in missing_synsets.items()])




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