import numpy as np

from omnigibson.object_states.link_based_state_mixin import LinkBasedStateMixin
from omnigibson.object_states.object_state_base import AbsoluteObjectState
from omnigibson.object_states.toggle import ToggledOn
from omnigibson.object_states.update_state_mixin import UpdateStateMixin


class FluidSource(AbsoluteObjectState, LinkBasedStateMixin, UpdateStateMixin):
    def __init__(self, obj):
        super().__init__(obj)

        # Initialize variables that will be filled in at runtime
        self._step_counter = None

    @property
    def fluid_system(self):
        """
        Returns:
            FluidSystem: Fluid system to use to generate / handle fluid particles
        """
        raise NotImplementedError

    @property
    def n_particles_per_group(self):
        """
        Returns:
            int: How many fluid particles to generate per fluid group
        """
        raise NotImplementedError

    @property
    def n_steps_per_group(self):
        """
        Returns:
            int: How many update() steps to occur between fluid group generations
        """
        raise NotImplementedError

    @staticmethod
    def get_state_link_name():
        # Should be implemented by subclass
        raise NotImplementedError

    def _initialize(self):
        super()._initialize()
        self.initialize_link_mixin()
        fluid_source_position = self.get_link_position()
        if fluid_source_position is None:
            return

        # Further initialize internal variables
        self._step_counter = 0

    def _update(self):
        fluid_source_position = self.get_link_position()
        if fluid_source_position is None or not self._simulator.is_playing():
            # Terminate early, this is a "dead" fluid source or we're not stepping physics
            return

        # Possibly increment our fluid generation counter if we're either (a) not using any toggle state (i.e.:
        # fluid source is always on), or (b) toggledon is True
        self._step_counter += int(self.obj.states[ToggledOn].get_value()) if ToggledOn in self.obj.states else 1

        # If our counter reaches our threshold, we generate a new fluid group
        if self._step_counter == self.n_steps_per_group:
            # Create positions to generate particles at
            positions = np.ones((self.n_particles_per_group, 3)) * fluid_source_position.reshape(1, 3)
            # Modify the z direction procedurally, to simulated a "falling" stream of fluid
            particle_dist = self.fluid_system.particle_contact_offset * 2
            positions[:, -1] -= np.arange(0, particle_dist * self.n_particles_per_group, particle_dist)
            # Add new particles to the system's default instancer
            self.fluid_system.default_particle_instancer.add_particles(positions=positions)

            # Reset the counter
            self._step_counter = 0

    def _set_value(self, new_value):
        raise ValueError("set_value not supported for FluidSource.")

    def _get_value(self):
        pass

    @staticmethod
    def get_optional_dependencies():
        return [ToggledOn]

    @staticmethod
    def get_dependencies():
        return []
