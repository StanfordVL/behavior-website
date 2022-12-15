from omnigibson.object_states.fluid_source import FluidSource
from omnigibson.systems.micro_particle_system import WaterSystem


class WaterSource(FluidSource):

    @property
    def fluid_system(self):
        return WaterSystem

    @property
    def n_particles_per_group(self):
        return 5

    @property
    def n_steps_per_group(self):
        return 5

    @staticmethod
    def get_state_link_name():
        return "watersource_link"
