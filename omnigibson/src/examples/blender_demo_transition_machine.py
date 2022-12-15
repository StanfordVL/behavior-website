import numpy as np
from scipy.spatial.transform import Rotation as R
from pxr import UsdShade, Sdf, Gf
import omnigibson as og
from omnigibson.macros import gm
from omnigibson.scenes import EmptyScene
from omnigibson.objects import USDObject, PrimitiveObject, LightObject, DatasetObject
from omnigibson.systems import WaterSystem, FluidSystem, MilkSystem, StrawberrySmoothieSystem
from omnigibson.utils.render_utils import make_glass
from omnigibson.utils.python_utils import classproperty
import omnigibson.utils.transform_utils as T
from omni.physx.scripts import particleUtils
import omni
import carb
from omni.usd import get_shader_from_material
from omni.isaac.core.utils.prims import get_prim_at_path
from PIL import Image
from pathlib import Path
import datetime
from collections import namedtuple, OrderedDict
from copy import deepcopy
import imageio

gm.ENABLE_CCD = True


def set_lights(intensity=None, rgb=None, ignore_keywords=None, n_steps=20):
    ignore_keywords = [] if ignore_keywords is None else ignore_keywords
    world = get_prim_at_path("/World")
    for prim in world.GetChildren():
        should_ignore = sum([ignore_keyword in prim.GetName() for ignore_keyword in ignore_keywords]) > 0
        if should_ignore:
            continue
        for prim_child in prim.GetChildren():
            for prim_child_child in prim_child.GetChildren():
                if "Light" in prim_child_child.GetPrimTypeInfo().GetTypeName():
                    print("Modifying light!")
                    if intensity is not None:
                        prim_child_child.GetAttribute("intensity").Set(intensity)
                    if rgb is not None:
                        prim_child_child.GetAttribute("color").Set(Gf.Vec3f(*rgb))

    for i in range(n_steps):
        og.sim.step()


def create_skylight():
    light = LightObject(prim_path="/World/skylight", name="skylight", radius=None, light_type="Dome", intensity=500)
    og.sim.import_object(light)
    light.set_orientation(T.euler2quat([0, 0, -np.pi / 4]))
    og.sim.play()
    og.sim.stop()
    light_prim = light.light_link.prim
    light_prim.GetAttribute("color").Set(Gf.Vec3f(1.07, 0.85, 0.61))
    # light_prim.GetAttribute("texture:file").Set(Sdf.AssetPath(f"{og.og_dataset_path}/../house_single_floor/scenes/house_single_floor/urdf/sky.jpg"))
    return light

og.sim.set_simulation_dt(physics_dt=1/120., rendering_dt=1/60.)

scene = EmptyScene()
og.sim.import_scene(scene)

# add skylight
skylight = create_skylight()




def take_photo(use_rt=None, name=f"{SCENE_ID}", rootdir=f"/home/cremebrule/tmp/og_photos/{SCENE_ID}"):
    # os.makedirs(os.path.dirname(rootdir), exist_ok=True)
    if use_rt is not None:
        if use_rt:
            set_rt()
        else:
            set_pt()
    Path(rootdir).mkdir(parents=True, exist_ok=True)
    img = cam.get_obs()["rgb"][:, :, :3]
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    Image.fromarray(img).save(f"{rootdir}/{name}_{og.app.config['renderer']}_{timestamp}.png")

    if use_rt is not None:
        set_rt()


class CameraMover:
    def __init__(self, cam, delta=0.25):
        self.cam = cam
        self.delta = delta

        self._appwindow = omni.appwindow.get_default_app_window()
        self._input = carb.input.acquire_input_interface()
        self._keyboard = self._appwindow.get_keyboard()
        self._sub_keyboard = self._input.subscribe_to_keyboard_events(self._keyboard, self._sub_keyboard_event)

    def print_cam_pose(self):
        print(f"cam pose: {self.cam.get_position_orientation()}")

    @property
    def input_to_function(self):
        return {
            carb.input.KeyboardInput.SPACE: lambda: take_photo(use_rt=True),
            carb.input.KeyboardInput.KEY_1: lambda: take_photo(use_rt=True),
            carb.input.KeyboardInput.KEY_2: lambda: take_photo(use_rt=False),
            carb.input.KeyboardInput.P: lambda: self.print_cam_pose(),
        }

    @property
    def input_to_command(self):
        return {
            carb.input.KeyboardInput.D: np.array([self.delta, 0, 0]),
            carb.input.KeyboardInput.A: np.array([-self.delta, 0, 0]),
            carb.input.KeyboardInput.W: np.array([0, 0, -self.delta]),
            carb.input.KeyboardInput.S: np.array([0, 0, self.delta]),
            carb.input.KeyboardInput.T: np.array([0, self.delta, 0]),
            carb.input.KeyboardInput.G: np.array([0, -self.delta, 0]),
        }

    def _sub_keyboard_event(self, event, *args, **kwargs):
        """Handle keyboard events
        Args:
            event (int): keyboard event type
        """
        if event.type == carb.input.KeyboardEventType.KEY_PRESS \
                or event.type == carb.input.KeyboardEventType.KEY_REPEAT:

            if event.type == carb.input.KeyboardEventType.KEY_PRESS and event.input in self.input_to_function:
                self.input_to_function[event.input]()

            else:
                command = self.input_to_command.get(event.input, None)

                if command is not None:
                    # Convert to world frame to move the camera
                    transform = T.quat2mat(self.cam.get_orientation())
                    delta_pos_global = transform @ command
                    self.cam.set_position(self.cam.get_position() + delta_pos_global)

        return True

cam = og.sim.viewer_camera
cam_mover = CameraMover(cam=cam)


# Command should be lambda with no args that executes something (e.g.: set pose, set joints, etc.)
TrajectoryCommand = namedtuple('TrajectoryCommand', ['cmd'])
TrajectoryWaypoint = namedtuple('TrajectoryWaypoint', ['n_steps', 'pose'])


class TrajectoryExecutor:
    def __init__(self):
        self.commands = OrderedDict()

    def add_commands(self, name, commands):
        assert isinstance(commands, list)
        assert isinstance(commands[0], TrajectoryCommand)

        if name not in self.commands:
            self.commands[name] = []

        self.commands[name] += commands

    def step(self):
        empty_cmd_names = []
        for name, cmds in self.commands.items():
            if len(cmds) == 0:
                empty_cmd_names.append(name)
            else:
                cmd = cmds.pop(0)
                cmd.cmd()

        # Remove any empty commands
        for name in empty_cmd_names:
            self.commands.pop(name)

    def clear(self):
        self.commands = OrderedDict()

    def save(self):
        return deepcopy(self.commands)

    def load(self, commands):
        self.commands = deepcopy(commands)


def convert_into_cmd(func, *func_args, **func_kwargs):
    return TrajectoryCommand(cmd=lambda: func(*func_args, **func_kwargs))


def euler2quat(euler, seq="xyz"):
    """
    Converts euler angles into quaternion form

    Args:
        euler (np.array): (r,p,y) angles

    Returns:
        np.array: (x,y,z,w) float quaternion angles

    Raises:
        AssertionError: [Invalid input shape]
    """
    return R.from_euler(seq, euler).as_quat()


def get_full_rotation_cam_trajectory_commands(center_pos, radius, tilt_angle, n_steps):
    # Generates trajectory commands to rotate camera 360 degrees about a specific point
    cmds = []
    dr = radius * np.cos(tilt_angle)
    dz = radius * np.sin(tilt_angle)
    for i in range(n_steps):
        pan_angle = i * 2 * np.pi / n_steps
        # Get orientation and pos
        dy = dr * np.cos(pan_angle)
        dx = dr * np.sin(pan_angle)
        pos = np.array(center_pos) + np.array([dx, -dy, dz])
        quat = euler2quat([np.pi / 2 - tilt_angle, pan_angle, 0.0], seq="xzy")
        cmds.append(convert_into_cmd(cam.set_position_orientation, position=pos, orientation=quat))

    return cmds


def get_light_spectrum_commands(start_intensity, min_intensity, max_intensity, modify_color=True, ignore_keywords=None, n_steps=100):
    # Split steps in half
    n_intensity_steps = int(n_steps // 2) if modify_color else n_steps
    n_color_steps = n_steps - n_intensity_steps if modify_color else 0
    cmds = []

    # Optionally add in color steps as well
    if n_color_steps > 0:
        # Eight cycles -- start with white, then lower all R, then lower G, then increase R, then lower B,
        # then increase G, then lower R, then increase B, then increase R back to white
        n_color_steps_eighth = int(n_color_steps // 8)
        n_color_remainder_steps = n_color_steps - n_color_steps_eighth * 8
        white2gb = np.linspace([1, 1, 1], [0, 1, 1], n_color_steps_eighth)
        gb2b = np.linspace([0, 1, 1], [0, 0, 1], n_color_steps_eighth)
        b2rb = np.linspace([0, 0, 1], [1, 0, 1], n_color_steps_eighth)
        rb2r = np.linspace([1, 0, 1], [1, 0, 0], n_color_steps_eighth)
        r2rg = np.linspace([1, 0, 0], [1, 1, 0], n_color_steps_eighth)
        rg2g = np.linspace([1, 1, 0], [0, 1, 0], n_color_steps_eighth)
        g2gb = np.linspace([0, 1, 0], [0, 1, 1], n_color_steps_eighth)
        gb2white = np.linspace([0, 1, 1], [1, 1, 1], n_color_steps_eighth + n_color_remainder_steps)

        # Add these color commands
        for color in np.concatenate([white2gb, gb2b, b2rb, rb2r, r2rg, rg2g, g2gb, gb2white], axis=0):
            cmds.append(convert_into_cmd(set_lights, intensity=None, rgb=color, ignore_keywords=ignore_keywords, n_steps=1))

    # Go through intensity in log scale
    n_intensity_steps_fourth = int(n_intensity_steps // 4)
    n_intensity_remainder_steps = n_intensity_steps - n_intensity_steps_fourth * 4

    # We go down from start, then all the way up, then back down
    intensity_down0 = np.logspace(np.log10(start_intensity), np.log10(min_intensity), n_intensity_steps_fourth)
    intensity_up = np.logspace(np.log10(min_intensity), np.log10(max_intensity), n_intensity_steps_fourth * 2)
    intensity_down1 = np.logspace(np.log10(max_intensity), np.log10(start_intensity), n_intensity_steps_fourth + n_intensity_remainder_steps)

    # Generate commands
    for intensity in np.concatenate([intensity_down0, intensity_up, intensity_down1]):
        cmds.append(convert_into_cmd(set_lights, intensity=intensity, rgb=None, ignore_keywords=ignore_keywords, n_steps=1))

    # Return the commands
    return cmds


def interpolate_pose(pos0, quat0, pos1, quat1, n_steps):
    # Get from pose0 --> pose1 in n_steps
    # Returns list of 2-tuple, where each entry is an interpolated value between the endpoints
    # Note: Does NOT include the start point
    vals = []
    pos_delta = (pos1 - pos0) / n_steps
    for i in range(n_steps):
        frac = (i + 1) / n_steps
        vals.append([
            pos0 + pos_delta * frac,
            T.quat_slerp(quat0, quat1, fraction=frac),
        ])

    return vals


def get_open_door_trajectory_commands(door, n_steps):
    # Gets required commands to open a door
    # Assumes lower limit of door is closed, upper limit is open
    # Note: Does NOT include start point
    low, high = door.joint_lower_limits, door.joint_upper_limits
    delta = high - low
    cmds = []
    for i in range(n_steps):
        frac = (i + 1) / n_steps
        cmds.append(TrajectoryCommand(cmd=lambda: door.set_joint_positions(low + delta * frac)))

    return cmds


def get_open_door_full_trajectory_commands(door, timestep_to_open, n_open_steps, n_total_steps):
    low, high = door.joint_lower_limits, door.joint_upper_limits
    start_cmd = TrajectoryCommand(cmd=lambda: door.set_joint_positions(low))
    end_cmd = TrajectoryCommand(cmd=lambda: door.set_joint_positions(high))
    open_cmds = get_open_door_trajectory_commands(door=door, n_steps=n_open_steps)
    return [start_cmd] * timestep_to_open + open_cmds + [end_cmd] * (n_total_steps - n_open_steps - timestep_to_open)


def generate_scheduled_cmds(timing_to_cmds):
    # timing_to_cmds should map step number (int) to list of cmd dictionaries to add to traj_exec
    max_count = int(np.max(list(timing_to_cmds.keys())))
    cmds = []
    for i in range(max_count + 1):
        if i in timing_to_cmds:
            cmds.append(convert_into_cmd(traj_exec.add_command_dicts, cmd_dicts=timing_to_cmds[i]))
        else:
            cmds.append(TrajectoryCommand(cmd=lambda: None))

    return cmds

def generate_trajectory_commands_from_waypoints(obj, waypoints):
    cmds = []
    start_pose = waypoints[0].pose
    cmds.append(TrajectoryCommand(cmd=lambda: obj.set_position_orientation(*start_pose)))
    for waypoint in waypoints[1:]:
        end_pose = waypoint.pose
        poses = interpolate_pose(*start_pose, *end_pose, n_steps=waypoint.n_steps)
        for pose in poses:
            cmds.append(TrajectoryCommand(cmd=lambda: obj.set_position_orientation(*pose)))
    return cmds


# cam_waypoints = [
#     TrajectoryWaypoint(n_steps=50, pose=[]),
#     TrajectoryWaypoint(n_steps=50, pose=[]),
# ]

# Create trajectory executor
traj_exec = TrajectoryExecutor()

# # Get camera commands
# # This determines how long the entire trajectory will be
# cam_cmds = generate_trajectory_commands_from_waypoints(obj=cam, waypoints=cam_waypoints)
# n_traj_steps = len(cam_cmds)
# traj_exec.add_commands(name=cam.name, commands=cam_cmds)


# n_open_steps = 25
# doors_open_timestep = [
#     [door, 25],
#     [door, 175],
# ]
#
# # Generate door commands
# for door, open_timestep in doors_open_timestep:
#     cmds = get_open_door_full_trajectory_commands(door, open_timestep, n_open_steps, n_traj_steps)
#     traj_exec.add_commands(name=door.name, commands=cmds)


# # Store commands
# all_commands = traj_exec.save()


def demo_traj(commands):
    traj_exec.clear()
    traj_exec.load(commands=commands)

    while traj_exec.commands:
        traj_exec.step()
        og.sim.step()



def record_traj(commands, save_fpath, fps=30):
    traj_exec.clear()
    traj_exec.load(commands=commands)

    video_writer = imageio.get_writer(save_fpath, fps=fps)

    while traj_exec.commands:
        traj_exec.step()
        og.sim.step()
        rgb = cam.get_obs()["rgb"][:, :, :-1]
        video_writer.append_data(rgb)

    video_writer.close()

def reset():
    og.sim.stop()
    og.sim.step()
    og.sim.play()


# Add bar
bar = USDObject(
    prim_path="/World/bar",
    name="bar",
    usd_path=f"{og.og_dataset_path}/../house_single_floor/objects/bar/pmvkyd/usd/pmvkyd.usd",
    # fixed_base=True,
    category="bar",
    visual_only=True,
    scale=[1, 0.5, 1],
)

og.sim.import_object(bar)
bar.set_position([0, 0, 0.65])

obj = USDObject(
    prim_path="/World/obj",
    name="obj",
    usd_path=f"{og.og_dataset_path}/../og_dataset/objects/blender/dhfqid/usd/dhfqid.usd",
    category="blender",
    fixed_base=True,
    abilities={"fillable": {}},
)

og.sim.import_object(obj)

# obj.set_position([0, 0, 0.17795013])
obj.set_position_orientation(
    bar.get_position() + np.array([0, 0, 5.06363420e-01]),
    np.array([0, 0, -0.707, -0.707]),
)

# Add light
light = LightObject("/World/light", name="light", light_type="Sphere", radius=0.001, intensity=5000)
og.sim.import_object(light)
light.set_position(obj.get_position() + np.array([-2.89317984e-02,  4.94765839e-10,  1.81066632e-01]))#np.array([3.29350009e-02, 4.65661648e-10, 1.83782876e-01]))

light1 = LightObject("/World/light1", name="light1", light_type="Sphere", radius=0.001, intensity=5000)
og.sim.import_object(light1)
light1.set_position(obj.get_position() + np.array([2.89317984e-02,  -4.94765839e-10,  1.81066632e-01]))#np.array([3.29350009e-02, 4.65661648e-10, 1.83782876e-01]))

light2 = LightObject("/World/light2", name="light2", light_type="Sphere", radius=0.001, intensity=5000)
og.sim.import_object(light2)
light2.set_position(obj.get_position() + np.array([-4.94765839e-10,  2.89317984e-02,  1.81066632e-01]))#np.array([3.29350009e-02, 4.65661648e-10, 1.83782876e-01]))

light3 = LightObject("/World/light3", name="light3", light_type="Sphere", radius=0.001, intensity=5000)
og.sim.import_object(light3)
light3.set_position(obj.get_position() + np.array([4.94765839e-10,  -2.89317984e-02,  1.81066632e-01]))#np.array([3.29350009e-02, 4.65661648e-10, 1.83782876e-01]))


# Add milk
milk_cylinder = PrimitiveObject(
    prim_path="/World/milk_cylinder",
    name="milk_cylinder",
    primitive_type="Cylinder",
    radius=0.0375,
    height=0.07,
    visual_only=True,
)
og.sim.import_object(milk_cylinder)
milk_cylinder.set_position(obj.get_position() + np.array([0, 0, 0.4]))
og.sim.step()
milk_cylinder.visible = False

# Add strawberries
strawberries = []
for i in range(5):
    strawberry = DatasetObject(
        prim_path=f"/World/strawberry{i}",
        name=f"strawberry{i}",
        category="strawberry",
        model="36_1",
        # usd_path=f"{og.og_dataset_path}/../og_dataset/objects/strawberry/36_1/usd/36_1.usd",
    )
    og.sim.import_object(strawberry)
    strawberries.append(strawberry)

# Move the strawberries out of the scene
for i, strawberry in enumerate(strawberries):
    strawberry.root_link.mass = 0.02
    strawberry.root_link.ccd_enabled = True
    strawberry.set_position(np.array([100., 100., 0.025 * i]))

# Add ice cubes
ice_cubes = []
for i in range(5):
    ice_cube = DatasetObject(
        prim_path=f"/World/ice_cube{i}",
        name=f"ice_cube{i}",
        category="ice_cube",
        model="ice_cube_000",
        # usd_path=f"{og.og_dataset_path}/../og_dataset/objects/ice_cube/ice_cube_000/usd/ice_cube_000.usd",
        scale=0.015,
    )
    og.sim.import_object(ice_cube)
    ice_cubes.append(ice_cube)

# Move the ice_cubes out of the scene
for i, ice_cube in enumerate(ice_cubes):
    make_glass(ice_cube)
    ice_cube.root_link.mass = 0.02
    ice_cube.root_link.ccd_enabled = True
    ice_cube.set_position(np.array([105., 105., 0.025 * i]))


make_glass(obj.links["glass"])
obj.links["lid"].visual_only = True

og.sim.enable_viewer_camera_teleoperation()
og.sim.play()
og.sim.step()

system = MilkSystem
container_mesh = milk_cylinder.root_link.visual_meshes["visual"]
system.prim.GetProperty("maxVelocity").Set(1.0)

milk_inst = MilkSystem.generate_particle_instancer_from_link(
    obj=milk_cylinder,
    link=milk_cylinder.root_link,
    idn=0,
    particle_group=0,
    # sampling_distance=0.02,
)
# milk_inst.set_attribute("physxParticle:particleEnabled", False)
# milk_inst.visible = False
# milk_cylinder.visible = False
#
# system = StrawberrySmoothieSystem
# container_mesh = obj.links["container_link"].visual_meshes["container_cylinder"]
# system.prim.GetProperty("maxVelocity").Set(1.0)
# smoothie_inst = system.generate_particle_instancer_from_mesh(
#     idn=0,
#     particle_group=0,
#     mesh_prim_path=container_mesh.prim_path,
#     # sampling_distance=0.02,
# )
# smoothie_inst.set_attribute("physxParticle:particleEnabled", False)
# smoothie_inst.visible = False
# container_mesh.visible = False
#
# og.sim.play()
# og.sim.step()
# og.sim.stop()

og.sim.viewer_camera.set_position_orientation(
    np.array([ 0.805484, -0.50198 ,  1.45247 ]),
    np.array([0.57064551, 0.32436113, 0.37280489, 0.65587352]),
)

og.sim.play()

# Scene: first open lid, then pour milk, then strawberries, then ice

# Demo scene
def demo_smoothie():
    og.sim.stop()

    # Clear all particles
    MilkSystem.remove_all_particle_instancers()
    StrawberrySmoothieSystem.remove_all_particle_instancers()

    # milk_inst.set_attribute("physxParticle:particleEnabled", False)
    # milk_inst.visible = False
    #
    # smoothie_inst.set_attribute("physxParticle:particleEnabled", False)
    # smoothie_inst.visible = False

    for i, strawberry in enumerate(strawberries):
        # og.sim.remove_object(strawberry)
        strawberry.set_position(np.array([100., 100., 0.025 * i]))

    for i, ice_cube in enumerate(ice_cubes):
        # og.sim.remove_object(ice_cube)
        ice_cube.set_position(np.array([105., 105., 0.025 * i]))

    og.sim.play()

    # Open lid
    obj.set_joint_positions(np.array([2.1816604]))

    for i in range(10):
        og.sim.step()

    # Pour milk via sampling
    # milk_inst.visible = True
    # milk_inst.set_attribute("physxParticle:particleEnabled", True)

    milk_mesh = milk_cylinder.root_link.visual_meshes["visual"]
    # system.prim.GetProperty("maxVelocity").Set(1.0)
    milk_inst = MilkSystem.generate_particle_instancer_from_link(
        obj=milk_cylinder,
        link=milk_cylinder.root_link,
        idn=0,
        particle_group=0,
        # sampling_distance=0.02,
    )

    for i in range(100):
        og.sim.step()

    # Pour strawberries

    # Move the strawberries to be above the blender
    height = 0.30
    for i, strawberry in enumerate(strawberries):
        strawberry.set_position(obj.get_position() + np.array([0, 0, height + 0.025]))
        strawberry.keep_still()
        for j in range(10):
            og.sim.step()

    for i in range(50):
        og.sim.step()

    # Pour ice cubes

    # Move the ice_cubes to be above the blender
    for i, ice_cube in enumerate(ice_cubes):
        ice_cube.set_position(obj.get_position() + np.array([0, 0, height]))
        ice_cube.keep_still()
        for j in range(10):
            og.sim.step()

    for i in range(50):
        og.sim.step()

    # Close lid
    for i in range(50):
        obj.set_joint_positions(obj.joint_upper_limits - obj.joint_range * (i + 1) / 50.0)
        og.sim.step()

    for i in range(20):
        obj.set_joint_positions(np.zeros(1))
        og.sim.step()

    # # Transform into strawberry smoothie!
    # milk_inst.set_attribute("physxParticle:particleEnabled", False)
    # milk_inst.visible = False
    #
    # for i, strawberry in enumerate(strawberries):
    #     # og.sim.remove_object(strawberry)
    #     strawberry.set_position(np.array([100., 100., 0.025 * i]))
    #
    # for i, ice_cube in enumerate(ice_cubes):
    #     # og.sim.remove_object(ice_cube)
    #     ice_cube.set_position(np.array([105., 105., 0.025 * i]))
    #
    # og.sim.step_physics()
    # smoothie_inst.set_attribute("physxParticle:particleEnabled", True)
    # smoothie_inst.visible = True

    for i in range(50):
        obj.set_joint_positions(np.zeros(1))
        og.sim.step()


def generate_smoothie_commands():
    cmds = []

    def reset_smoothie():
        og.sim.stop()

        milk_inst.set_attribute("physxParticle:particleEnabled", False)
        milk_inst.visible = False

        smoothie_inst.set_attribute("physxParticle:particleEnabled", False)
        smoothie_inst.visible = False

        for i, strawberry in enumerate(strawberries):
            # og.sim.remove_object(strawberry)
            strawberry.set_position(np.array([100., 100., 0.025 * i]))

        for i, ice_cube in enumerate(ice_cubes):
            # og.sim.remove_object(ice_cube)
            ice_cube.set_position(np.array([105., 105., 0.025 * i]))

        og.sim.play()

        # Open lid
        obj.set_joint_positions(np.array([2.1816604]))

        og.sim.step()
        og.sim.render()
        og.sim.render()

    cmds.append(convert_into_cmd(reset_smoothie))

    for i in range(10):
        cmds.append(convert_into_cmd(og.sim.step))

    # Pour milk
    def toggle_milk_enabled(enabled):
        milk_inst.visible = enabled
        milk_inst.set_attribute("physxParticle:particleEnabled", enabled)

    cmds.append(convert_into_cmd(toggle_milk_enabled, enabled=True))

    for i in range(100):
        cmds.append(convert_into_cmd(og.sim.step))

    # Pour strawberries

    def spawn_strawberry(idx):
        strawberries[idx].set_position(obj.get_position() + np.array([0, 0, 0.35 + 0.025]))
        strawberries[idx].keep_still()

    # Move the strawberries to be above the blender
    for i, strawberry in enumerate(strawberries):
        cmds.append(convert_into_cmd(spawn_strawberry, idx=i))
        for j in range(10):
            cmds.append(convert_into_cmd(og.sim.step))

    for i in range(50):
        cmds.append(convert_into_cmd(og.sim.step))

    # Pour ice cubes

    def spawn_ice_cube(idx):
        ice_cubes[idx].set_position(obj.get_position() + np.array([0, 0, 0.35]))
        ice_cubes[idx].keep_still()

    # Move the ice_cubes to be above the blender
    for i, ice_cube in enumerate(ice_cubes):
        cmds.append(convert_into_cmd(spawn_ice_cube, idx=i))
        for j in range(10):
            cmds.append(convert_into_cmd(og.sim.step))

    for i in range(50):
        cmds.append(convert_into_cmd(og.sim.step))

    def set_blender_lid_qpos(qpos):
        obj.set_joint_positions(qpos)
        og.sim.step()

    # Close lid
    for i in range(50):
        cmds.append(convert_into_cmd(set_blender_lid_qpos, qpos=obj.joint_upper_limits - obj.joint_range * (i + 1) / 50.0))

    for i in range(20):
        cmds.append(convert_into_cmd(set_blender_lid_qpos, qpos=np.zeros(1)))

    # Transform into strawberry smoothie!
    cmds.append(convert_into_cmd(toggle_milk_enabled, enabled=False))

    def remove_strawberries_and_ice_cubes():
        for i, strawberry in enumerate(strawberries):
            # og.sim.remove_object(strawberry)
            strawberry.set_position(np.array([100., 100., 0.025 * i]))

        for i, ice_cube in enumerate(ice_cubes):
            # og.sim.remove_object(ice_cube)
            ice_cube.set_position(np.array([105., 105., 0.025 * i]))
        og.sim.step_physics()

    cmds.append(convert_into_cmd(remove_strawberries_and_ice_cubes))

    def toggle_smoothie_enabled(enabled):
        smoothie_inst.visible = enabled
        smoothie_inst.set_attribute("physxParticle:particleEnabled", enabled)

    cmds.append(convert_into_cmd(toggle_smoothie_enabled, enabled=True))

    for i in range(50):
        cmds.append(convert_into_cmd(set_blender_lid_qpos, qpos=np.zeros(1)))

    return cmds


n_rotation_steps = 1200


# smoothie + rotation
obj_pos = obj.get_position()
smoothie_cmds = OrderedDict(smoothie=generate_smoothie_commands())
rotate_cmds = OrderedDict(rotate=get_full_rotation_cam_trajectory_commands(obj_pos + np.array([0, 0, 0.18]), 0.949, np.pi / 15, n_steps=n_rotation_steps)[:len(smoothie_cmds["smoothie"])])
rotate_cmds.update(smoothie_cmds)



# # 1, 0.64, 0.64, 0.3 emission, no transmission, only base + emission
# shader = get_shader_from_material(StrawberrySmoothieSystem.particle_material.GetPrim())
# # shader.CreateInput("diffuse_reflection_color", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f([1.0, 0.64, 0.64]))
# shader.CreateInput("specular_reflection_color", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f([1.0, 0.64, 0.64]))

marker = PrimitiveObject(
    prim_path="/World/marker",
    name="marker",
    primitive_type="Sphere",
    scale=0.001,
    visual_only=True,
    rgba=[0, 1.0, 1.0, 1.0],
)
og.sim.import_object(marker)
marker.set_position([0, 0, 1.5])
