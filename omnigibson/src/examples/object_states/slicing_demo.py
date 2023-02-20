import logging
import numpy as np

import omnigibson as og
from omnigibson.macros import gm
import omnigibson.utils.transform_utils as T

# Make sure object states, contact reporting, and transition rules are enabled
gm.ENABLE_OBJECT_STATES = True
gm.ENABLE_GLOBAL_CONTACT_REPORTING = True
gm.ENABLE_TRANSITION_RULES = True


def main(random_selection=False, headless=False, short_exec=False):
    """
    Demo to use the raycasting-based sampler to load objects onTop and/or inside another
    Loads a cabinet, a microwave open on top of it, and two plates with apples on top, one inside and one on top of the cabinet
    Then loads a shelf and cracker boxes inside of it
    """
    logging.info("*" * 80 + "\nDescription:" + main.__doc__ + "*" * 80)

    # Create the scene config to load -- empty scene with table, knife, and apple
    table_cfg = dict(
        type="DatasetObject",
        name="table",
        category="breakfast_table",
        model="19203",
        scale=0.9,
        position=[0, 0, 0.532],
    )

    apple_cfg = dict(
        type="DatasetObject",
        name="apple",
        category="apple",
        model="00_0",
        scale=1.5,
        position=[0.085, 0,  0.90],
    )

    knife_cfg = dict(
        type="DatasetObject",
        name="knife",
        category="table_knife",
        model="4",
        scale=2.5,
        position=[0, 0, 10.0],
    )

    light0_cfg = dict(
        type="LightObject",
        name="light0",
        light_type="Sphere",
        radius=0.01,
        intensity=4000.0,
        position=[1.217, -0.848, 1.388],
    )

    light1_cfg = dict(
        type="LightObject",
        name="light1",
        light_type="Sphere",
        radius=0.01,
        intensity=4000.0,
        position=[-1.217, 0.848, 1.388],
    )

    cfg = {
        "scene": {
            "type": "Scene",
        },
        "objects": [table_cfg, apple_cfg, knife_cfg, light0_cfg, light1_cfg]
    }

    # Create the environment
    env = og.Environment(configs=cfg, action_timestep=1/60., physics_timestep=1/60.)

    # Grab reference to apple and knife
    apple = env.scene.object_registry("name", "apple")
    knife = env.scene.object_registry("name", "knife")

    # Update the simulator's viewer camera's pose so it points towards the table
    og.sim.viewer_camera.set_position_orientation(
        position=np.array([ 0.544888, -0.412084,  1.11569 ]),
        orientation=np.array([0.54757518, 0.27792802, 0.35721896, 0.70378409]),
    )

    # Let apple settle
    for _ in range(50):
        env.step(np.array([]))

    knife.keep_still()
    knife.set_position_orientation(
        position=apple.get_position() + np.array([-0.15, 0.0, 0.2]),
        orientation=T.euler2quat([-np.pi / 2, 0, 0]),
    )

    input("The knife will fall on the apple and slice it. Press [ENTER] to continue.")

    # Step simulation for a bit so that apple is sliced
    for i in range(1000):
        env.step(np.array([]))

    input("Apple has been sliced! Press [ENTER] to terminate the demo.")

    # Always close environment at the end
    env.close()


if __name__ == "__main__":
    main()
