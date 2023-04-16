from flask import Flask, render_template, abort
from data import *


G = get_all_synsets()
scene_to_objects = get_all_scenes()
object_to_fn, cat_to_object, provided_categories = get_all_objects_and_categories(scene_to_objects)
cat_to_synset, synset_to_cat = get_category_synset_mapping(provided_categories)
tasks_to_fn = get_all_tasks()
task_to_synset, synset_to_task, task_to_scene_synset, task_to_non_scene_synset, task_to_legal_synsets, task_to_illegal_synsets, task_requirements = get_task_synset_mapping(G, tasks_to_fn)
task_to_scene = get_task_scene_mapping(G, tasks_to_fn, scene_to_objects, task_requirements)
synset_to_objects, task_to_found_synset, task_to_not_found_synset = get_available_synsets(G, synset_to_cat, task_to_legal_synsets, cat_to_object)
tasks_status = {
    task_name: [task_to_illegal_synsets[task_name], task_to_scene[task_name], task_to_found_synset[task_name], task_to_not_found_synset[task_name]] for task_name in tasks_to_fn
}

# ==================================================================================================

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', tasks_status=tasks_status)


@app.route('/task/<task_name>')
def task(task_name):
    task_data = tasks_status[task_name]
    if not task_data:
        abort(404)
    return render_template('task.html', task_name=task_name, task_data=task_data)


@app.route('/objects')
def objects():
    return render_template('objects.html', synset_to_task=synset_to_task, synset_to_objects=synset_to_objects)


@app.template_filter('format_iterable')
def format_list(lst):
    return ', '.join(str(x) for x in lst)


if __name__ == '__main__':
    app.run()