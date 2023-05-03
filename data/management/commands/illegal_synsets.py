import json
from data.utils import *
from data.models import *
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "generates task-scene mapping csv and missing synsets csv"

    def handle(self, *args, **options):
        illegal_synsets = sorted(list(Synset.objects.filter(state=STATE_ILLEGAL).values_list("name", flat=True)))
        with open("output/all_illegal_synsets.json", "w") as f:
            json.dump(illegal_synsets, f, indent=4)
        