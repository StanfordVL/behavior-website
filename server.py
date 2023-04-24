import argparse
from flask import Flask, render_template, abort
from data import *
from flask_frozen import Freezer

import nltk
nltk.download('wordnet')

G = get_all_synsets()
tasks_to_fn = get_tasks()
all_scenes, cur_scenes = get_scenes()
all_objects, cur_objects, all_cat_to_object, cur_cat_to_object, all_categories, cur_categories = get_objects_and_categories()
all_cat_to_synset, cur_cat_to_synset, all_synset_to_cat, cur_synset_to_cat = get_category_synset_mapping(all_categories, cur_categories)
task_to_synset, synset_to_task, task_to_scene_synset, task_to_non_scene_synset, task_to_legal_synsets, task_to_illegal_synsets, task_requirements = get_task_synset_mapping(G, tasks_to_fn)
all_task_to_scene, cur_task_to_scene = get_task_scene_mapping(G, tasks_to_fn, all_scenes, cur_scenes, task_requirements)
all_synset_to_objects, cur_synset_to_objects, all_task_to_found_synset, cur_task_to_found_synset, all_task_to_not_found_synset, cur_task_to_not_found_synset = \
    get_available_synsets(G, task_to_legal_synsets, all_synset_to_cat, cur_synset_to_cat, all_cat_to_object, cur_cat_to_object)

# construct task status
tasks_status = {
    task_name: [
        task_to_illegal_synsets[task_name], 
        cur_task_to_scene[task_name], 
        cur_task_to_found_synset[task_name],
        cur_task_to_not_found_synset[task_name],
        all_task_to_scene[task_name], 
        all_task_to_found_synset[task_name],
        all_task_to_not_found_synset[task_name],
    ] for task_name in tasks_to_fn
}

# metadata
n_success_task = len([x for x in tasks_status if len(tasks_status[x][0]) == 0 and len(tasks_status[x][1]) > 0 and len(tasks_status[x][3]) == 0])
n_pending_task = len([x for x in tasks_status if len(tasks_status[x][0]) == 0 and len(tasks_status[x][4]) > 0 and len(tasks_status[x][6]) == 0])
n_success_synset = len([x for x in all_synset_to_cat if len(cur_synset_to_objects[x]) > 0])
n_pending_synset = len([x for x in all_synset_to_cat if len(all_synset_to_objects[x]) > 0])

metadata = [
    [n_success_task, n_pending_task, len(tasks_to_fn)],             # tasks
    [n_success_synset, n_pending_synset, len(all_synset_to_cat)],   # synsets
    [len(cur_objects), len(all_objects)],                           # objects 
    [len(cur_scenes), len(all_scenes)]                              # scenes
]


# ==================================================================================================
parser = argparse.ArgumentParser(description='Generate static website for the dataset')
parser.add_argument('-d', '--debug', action='store_true', help='debug mode (build local server)')
args = parser.parse_args()
prefix = "" if args.debug else "/b1k-integration"

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', metadata=metadata, prefix=prefix)


@app.route('/tasks/')
def tasks_list():
    return render_template('tasks_list.html', tasks_status=tasks_status, prefix=prefix)


@app.route('/tasks/<task_name>.html')
def tasks(task_name):
    task_data = tasks_status[task_name]
    if not task_data:
        abort(404)
    return render_template('task.html', task_name=task_name, task_data=task_data)


@app.route('/synsets.html')
def objects():
    return render_template('synsets.html', synset_to_task=synset_to_task, all_synset_to_objects=all_synset_to_objects, cur_synset_to_objects=cur_synset_to_objects)


@app.template_filter('format_iterable')
def format_list(iter):
    return ', '.join(str(x) for x in iter)


if __name__ == '__main__':
    if args.debug:
        print("Building local webserver...")
        app.debug = True
        app.run()
    else:
        print("Generating static website files...")
        freezer = Freezer(app)
        freezer.freeze()
