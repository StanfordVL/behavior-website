import csv
from tqdm import tqdm
from data.utils import *
from data.models import *
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "generates task-scene mapping csv and missing synsets csv"

    def handle(self, *args, **options):
        # get missing synsets csv
        with open('output/missing_synsets.csv', 'w', newline='') as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow(["synset", "required task", "is substance"])
            for synset in tqdm(Synset.objects.all()):
                if synset.task_set.count() != 0:
                    if len(synset.matching_objects) == 0:
                        csv_writer.writerow([
                            synset.name,
                            ",".join([task.name for task in synset.task_set.all()]),
                            synset.is_substance,
                        ])
                        
        # # get task-scene mapping csv
        with open('output/task_scene_matching.csv', 'w', newline='') as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow(["task", "matched scenes", "synset matched"])
            for task in tqdm(Task.objects.all()):   
                result = task.scene_matching_dict
                synset_state = True if task.synset_state == STATE_MATCHED else False
                csv_writer.writerow([
                    task.name,
                    ",".join(result["matched"].keys()),
                    synset_state,
                ])
        