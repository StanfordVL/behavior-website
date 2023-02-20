from omnigibson.macros import create_module_macros
from omnigibson.object_states.aabb import AABB
from omnigibson.object_states.inside import Inside
from omnigibson.object_states.link_based_state_mixin import LinkBasedStateMixin
from omnigibson.object_states.object_state_base import AbsoluteObjectState
from omnigibson.object_states.open import Open
from omnigibson.object_states.toggle import ToggledOn


# Create settings for this module
m = create_module_macros(module_path=__file__)

m.HEATING_ELEMENT_LINK_NAME = "heatsource_link"

m.HEATING_ELEMENT_MARKER_SCALE = [1.0] * 3
# m.HEATING_ELEMENT_MARKER_FILENAME = os.path.join(omnigibson.assets_path, "models/fire/fire.obj")

# TODO: Delete default values for this and make them required.
m.DEFAULT_TEMPERATURE = 200
m.DEFAULT_HEATING_RATE = 0.04
m.DEFAULT_DISTANCE_THRESHOLD = 0.2


class HeatSourceOrSink(AbsoluteObjectState, LinkBasedStateMixin):
    """
    This state indicates the heat source or heat sink state of the object.

    Currently, if the object is not an active heat source/sink, this returns (False, None).
    Otherwise, it returns True and the position of the heat source element, or (True, None) if the heat source has no
    heating element / only checks for Inside.
    E.g. on a stove object, True and the coordinates of the heating element will be returned.
    on a microwave object, True and None will be returned.
    """

    def __init__(
        self,
        obj,
        temperature=m.DEFAULT_TEMPERATURE,
        heating_rate=m.DEFAULT_HEATING_RATE,
        distance_threshold=m.DEFAULT_DISTANCE_THRESHOLD,
        requires_toggled_on=False,
        requires_closed=False,
        requires_inside=False,
    ):
        """
        Args:
            obj (StatefulObject): The object with the heat source ability.
            temperature (float): The temperature of the heat source.
            heating_rate (float): Fraction in [0, 1] of the temperature difference with the
                heat source temperature should be received every step, per second.
            distance_threshold (float): The distance threshold which an object needs
                to be closer than in order to receive heat from this heat source.
            requires_toggled_on (bool): Whether the heat source object needs to be
                toggled on to emit heat. Requires toggleable ability if set to True.
            requires_closed (bool): Whether the heat source object needs to be
                closed (e.g. in terms of the joints) to emit heat. Requires openable
                ability if set to True.
            requires_inside (bool): Whether an object needs to be `inside` the
                heat source to receive heat. See the Inside state for details. This
                will mean that the "heating element" link for the object will be
                ignored.
        """
        super(HeatSourceOrSink, self).__init__(obj)
        self.temperature = temperature
        self.heating_rate = heating_rate
        self.distance_threshold = distance_threshold

        # If the heat source needs to be toggled on, we assert the presence
        # of that ability.
        if requires_toggled_on:
            assert ToggledOn in self.obj.states
        self.requires_toggled_on = requires_toggled_on

        # If the heat source needs to be closed, we assert the presence
        # of that ability.
        if requires_closed:
            assert Open in self.obj.states
        self.requires_closed = requires_closed

        # If the heat source needs to contain an object inside to heat it,
        # we record that for use in the heat transfer process.
        self.requires_inside = requires_inside

    @staticmethod
    def get_dependencies():
        return AbsoluteObjectState.get_dependencies() + [AABB, Inside]

    @staticmethod
    def get_optional_dependencies():
        return AbsoluteObjectState.get_optional_dependencies() + [ToggledOn, Open]

    @staticmethod
    def get_state_link_name():
        return m.HEATING_ELEMENT_LINK_NAME

    def _initialize(self):
        # Run super first
        super()._initialize()
        self.initialize_link_mixin()

    def _get_value(self):
        # if the object is not in self.requires_inside mode, the link position is required.
        if not self.requires_inside and self.get_link_position() is None:
            return False

        # Check the toggle state.
        if self.requires_toggled_on and not self.obj.states[ToggledOn].get_value():
            return False

        # Check the open state.
        if self.requires_closed and self.obj.states[Open].get_value():
            return False

        return True

    def _set_value(self, new_value):
        raise NotImplementedError("Setting heat source capability is not supported.")

    # Nothing needs to be done to save/load HeatSource
