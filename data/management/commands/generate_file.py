import csv
from tqdm import tqdm
from data.utils import *
from data.models import *
from django.core.management.base import BaseCommand

scene_name_filter = [
    "attach_a_camera_to_a_tripod",
    "boil_water",
    "chop_an_onion",
    "clean_up_broken_glass",
    "cleaning_bathtub",
    "fill_a_bucket_in_a_small_sink",
    "folding_piece_of_cloth",
    "freeze_pies",
    "hanging_up_bedsheets",
    "make_a_steak",
    "make_a_strawberry_slushie",
    "melt_white_chocolate",
    "mixing_drinks",
    "mowing_the_lawn",
    "putting_away_Halloween_decorations",
    "putting_away_toys",
    "putting_up_shelves",
    "setting_the_fire",
    "spraying_for_bugs",
    "thawing_frozen_food"
]

class Command(BaseCommand):
    help = "generates task-scene mapping csv and missing synsets csv"

    def handle(self, *args, **options):
        # get missing synsets csv
        with open('missing_synsets.csv', 'w', newline='') as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow(["synset", "required task", "is substance"])
            for synset in tqdm(Synset.objects.all()):
                if synset.task_set.count() != 0:
                    if len(synset.matching_object) == 0:
                        csv_writer.writerow([
                            synset.name,
                            ",".join([task.name for task in synset.task_set.all()]),
                            synset.is_substance,
                        ])
                        
        # # get task-scene mapping csv
        with open('task_scene_matching.csv', 'w', newline='') as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow(["task", "matched scenes", "planned scenes"])
            for task in tqdm(Task.objects.all()):   
                if task.name in scene_name_filter:   
                    result = task.scene_matching_dict
                    csv_writer.writerow([
                        task.name,
                        ",".join(result["matched"].keys()),
                        ",".join(result["planned"].keys())
                    ])
        