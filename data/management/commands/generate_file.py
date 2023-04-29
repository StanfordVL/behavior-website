import csv
from tqdm import tqdm
from data.utils import *
from data.models import *
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "generates task-scene mapping csv and missing synsets csv"

    def handle(self, *args, **options):
        # get missing synsets csv
        with open('missing_synsets.csv', 'w', newline='') as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow(["synset", "required task"])
            for synset in tqdm(Synset.objects.all()):
                if synset.task_set.count() != 0:
                    if len(synset.matching_ready_object) == 0:
                        csv_writer.writerow([
                            synset.name,
                            ",".join([task.name for task in synset.task_set.all()]),
                        ])
                        
        # # get task-scene mapping csv
        # with open('task_scene_matching.csv', 'w') as f:
        #     csv_writer = csv.writer(f)
        #     csv_writer.writerow(["task", "matched scenes", "planned scenes"])
        #     for task in tqdm(Task.objects.all()):      
        #         result = task.scene_matching_dict
        #         csv_writer.writerow([
        #             task.name,
        #             ",".join(result["matched"].keys()),
        #             ",".join(result["planned"].keys())
        #         ])
    