from lewis.devices import StateMachineDevice
from lewis.core import approaches
from .states import DefaultState
from collections import OrderedDict


class SimulatedCCD100(StateMachineDevice):

    def _initialize_data(self):
        self.initial_id_prefix = "1111"
        self.secondary_id_prefix = "1111"
        self.em_stop_status = 0  # Bool [0-1]
        self.run_bit = 0  # Bool [0-1]
        self.reset_value = 0
        self.stop_bit = 0  # Bool [0-1]\
        self.busy_bit = 0  # Bool [0-1]
        self.go_status = 0
        self.am_mode = 0
        self.loop_mode = 0  # Bool [0-1]
        self.seal_fail_value = 0
        self.last_error_code = 0
        self.pressure_rate = 0
        self.min_value_pre_servoing = 0
        self.setpoint_value = 0
        self.max_value_pre_servoing = 0

        # When the device is in an error state it can respond with junk
        self.is_giving_errors = False
        self.out_error = "}{<7f>w"
        self.out_terminator_in_error = ""

    def _get_state_handlers(self):
        return {
            'default': DefaultState(),
        }

    def _get_initial_state(self):
        return 'default'

    def _get_transition_handlers(self):
        return OrderedDict([])

