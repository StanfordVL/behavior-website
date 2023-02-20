import logging
import os

import yaml
import builtins

# TODO: Need to fix somehow -- omnigibson gets imported first BEFORE we can actually modify the macros
from omnigibson.macros import gm

builtins.ISAAC_LAUNCHED_FROM_JUPYTER = (
    os.getenv("ISAAC_JUPYTER_KERNEL") is not None
)  # We set this in the kernel.json file

# Always enable nest_asyncio because MaterialPrim calls asyncio.run()
import nest_asyncio
nest_asyncio.apply()

__version__ = "0.0.4"

logging.getLogger().setLevel(logging.INFO)

with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "global_config.yaml")) as f:
    global_config = yaml.load(f, Loader=yaml.FullLoader)

# can override assets_path and dataset_path from environment variable
if "OMNIGIBSON_ASSETS_PATH" in os.environ:
    assets_path = os.environ["OMNIGIBSON_ASSETS_PATH"]
else:
    assets_path = global_config["assets_path"]
assets_path = os.path.expanduser(assets_path)

if "GIBSON_DATASET_PATH" in os.environ:
    g_dataset_path = os.environ["GIBSON_DATASET_PATH"]
else:
    g_dataset_path = global_config["g_dataset_path"]
g_dataset_path = os.path.expanduser(g_dataset_path)

if "OMNIGIBSON_DATASET_PATH" in os.environ:
    og_dataset_path = os.environ["OMNIGIBSON_DATASET_PATH"]
else:
    og_dataset_path = global_config["og_dataset_path"]
og_dataset_path = os.path.expanduser(og_dataset_path)

if "OMNIGIBSON_KEY_PATH" in os.environ:
    key_path = os.environ["OMNIGIBSON_KEY_PATH"]
else:
    key_path = global_config["key_path"]
key_path = os.path.expanduser(key_path)

root_path = os.path.dirname(os.path.realpath(__file__))

if not os.path.isabs(assets_path):
    assets_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), assets_path)
if not os.path.isabs(g_dataset_path):
    g_dataset_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), g_dataset_path)
if not os.path.isabs(og_dataset_path):
    og_dataset_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), og_dataset_path)
if not os.path.isabs(key_path):
    key_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), key_path)

logging.info("Importing OmniGibson (omnigibson module)")
logging.info("Assets path: {}".format(assets_path))
logging.info("Gibson Dataset path: {}".format(g_dataset_path))
logging.info("OmniGibson Dataset path: {}".format(og_dataset_path))
logging.info("OmniGibson Key path: {}".format(key_path))

example_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "examples")
example_config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "configs")

logging.info("Example path: {}".format(example_path))
logging.info("Example config path: {}".format(example_config_path))

# whether to enable debugging mode for object sampling
debug_sampling = False

# Initialize global variables
app = None  # (this is a singleton so it's okay that it's global)
sim = None  # (this is a singleton so it's okay that it's global)
Environment = None
REGISTERED_SCENES = None
REGISTERED_OBJECTS = None
REGISTERED_ROBOTS = None
REGISTERED_CONTROLLERS = None
REGISTERED_TASKS = None
ALL_SENSOR_MODALITIES = None


# Helper functions for starting omnigibson
def print_save_usd_warning(_):
    logging.warning("Exporting individual USDs has been disabled in OG due to copyrights.")


def create_app():
    global app
    from omni.isaac.kit import SimulationApp
    app = SimulationApp({"headless": gm.HEADLESS})
    import omni

    # Possibly hide windows if in debug mode
    if not gm.DEBUG:
        hide_window_names = ["Console", "Main ToolBar", "Stage", "Layer", "Property", "Render Settings", "Content",
                             "Flow", "Semantics Schema Editor"]
        for name in hide_window_names:
            window = omni.ui.Workspace.get_window(name)
            if window is not None:
                window.visible = False
                app.update()

    omni.kit.widget.stage.context_menu.ContextMenu.save_prim = print_save_usd_warning

    return app


def create_sim():
    global sim
    from omnigibson.simulator import Simulator
    sim = Simulator()
    return sim


def start():
    global app, sim, Environment, REGISTERED_SCENES, REGISTERED_OBJECTS, REGISTERED_ROBOTS, REGISTERED_CONTROLLERS, \
        REGISTERED_TASKS, ALL_SENSOR_MODALITIES

    # First create the app, then create the sim
    app = create_app()
    sim = create_sim()

    # Import any remaining items we want to access directly from the main omnigibson import
    from omnigibson.envs import Environment
    from omnigibson.scenes import REGISTERED_SCENES
    from omnigibson.objects import REGISTERED_OBJECTS
    from omnigibson.robots import REGISTERED_ROBOTS
    from omnigibson.controllers import REGISTERED_CONTROLLERS
    from omnigibson.tasks import REGISTERED_TASKS
    from omnigibson.sensors import ALL_SENSOR_MODALITIES
    return app, sim, Environment, REGISTERED_SCENES, REGISTERED_OBJECTS, REGISTERED_ROBOTS, REGISTERED_CONTROLLERS, \
        REGISTERED_TASKS, ALL_SENSOR_MODALITIES


# Automatically start omnigibson's omniverse backend unless explicitly told not to
if not (os.getenv("OMNIGIBSON_NO_OMNIVERSE", 'False').lower() in {'true', '1', 't'}):
    app, sim, Environment, REGISTERED_SCENES, REGISTERED_OBJECTS, REGISTERED_ROBOTS, REGISTERED_CONTROLLERS, \
        REGISTERED_TASKS, ALL_SENSOR_MODALITIES = start()


def shutdown():
    global app
    app.close()
    exit(0)
