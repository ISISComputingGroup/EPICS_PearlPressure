import time
import threading
from lewis.devices import StateMachineDevice
from lewis.core import approaches
from .states import DefaultState
from collections import OrderedDict
from enum import Enum


class RESET_STATUS(Enum):
    """
    Enum class for the reset status of the device
    """
    NOT_RESETTING_OR_PURGING = 0
    RESET_COMPLETE = 1
    RESETTING = 2
    PURGE_DONE = 3
    PURGING = 4


class SimulatedPearlPC(StateMachineDevice):

    def _initialize_data(self, status_dictionary=None):
        if status_dictionary is None:
            status_dictionary = {}
        self.status_dictionary = status_dictionary
        self.re_initialise()

        # When the device is in an error state it can respond with junk
        self.is_giving_errors = False
        self.out_error = "}{<7f>w"
        self.out_terminator_in_error = ""

    def add_to_dict(self, value_id: str, unvalidated_value: object):
        """
        Add device state parameters to a dictionary.
        @param value_id: (str) dictionary key for each device parameter
        @param unvalidated_value: (object) device parameter set to describe system status
        """
        self.status_dictionary[value_id] = unvalidated_value

    def _get_state_handlers(self):
        return {
            'default': DefaultState(),
        }

    def _get_initial_state(self):
        return 'default'

    def _get_transition_handlers(self):
        return OrderedDict([])

    def re_initialise(self):
        self.connected = True

        self.initial_id_prefix = 1111  # 4 digits
        # "oil" or "pentane", set manually on the machine by the inst scientist
        self.fluid_type = "Pentane"
        self.secondary_id_prefix = 1111  # 4 digits
        self.em_stop_status = 0  # Bool [0-1]
        self.run_bit = 0  # Bool [0-1]
        self.reset_value = 0  # [0-4]
        self.piston_reset_phase = 0
        self.stop_bit = 0  # Bool [0-1]
        self.busy_bit = 0  # Bool [0-1]
        self.go_status = 0
        self.am_mode = 1  # auto mode (run from host) rather than manual
        self.loop_mode = 0  # Bool [0-1]
        self.seal_fail_value = 0
        self.seal_fail_status = 0  # set to 1 if sudden pressure drop more than seal_fail_value
        self.last_error_code = 0
        self.pressure_rate = 0
        self.min_value_pre_servoing = 0
        self.setpoint_value = 0
        self.max_value_pre_servoing = 0
        self.inputs = 0  # a 9 digit number like 111111001 showing input status
        self.cell_pressure = 0
        self.pump_pressure = 0
        self.transducer_difference_threshold = 2
        self.algorithm = "a"
        self.transducer = "0"
        self.user_stop_limit = 1000
        self.offset_plus = 0
        self.offset_minus = 0
        self.dir_plus = 0
        self.dir_minus = 0

        # for comms with poller thread
        self.run_requested = 0
        self.stop_requested = 0
        self.reset_requested = 0
        self.purge_requested = 0
        self.ramping = 0  # ramping to setpoint as opposed to closed loop stabilisation?

    def get_pressure(self):
        value = 0.0
        if self.algorithm == "a":
            value = (self.cell_pressure + self.pump_pressure) / 2.0
        elif self.algorithm == "1":
            value = self.cell_pressure
        elif self.algorithm == "2":
            value = self.pump_pressure
        elif self.algorithm == "h":
            value = max(self.pump_pressure, self.cell_pressure)
        elif self.algorithm == "l":
            value = min(self.pump_pressure, self.cell_pressure)
        elif self.algorithm[:1] == "w" and len(self.algorithm) == 3:
            weight = float(self.algorithm[1:3]) / 100.0
            value = weight * self.cell_pressure + \
                (1.0 - weight) * self.pump_pressure
        return int(value)

    def stop(self):
        self.stop_requested = 1

    def reset(self):
        self.reset_requested = 1

    def set_fluid_type(self, fluid_type: int):
        if fluid_type == 1:
            self.fluid_type = "Oil"
        elif fluid_type == 2:
            self.fluid_type = "Pentane"
        else: 
            self.fluid_type = "Not Set"

    def get_fluid_type(self):
        return self.fluid_type

    def purge(self):
        self.purge_requested = 1

    def run(self):
        self.run_requested = 1

    def poller(self):
        self.inputs = int("011110000") + int("000000001") * self.am_mode
        if self.reset_requested:
            if self.reset_value == RESET_STATUS.NOT_RESETTING_OR_PURGING.value:
                self.reset_value = RESET_STATUS.RESETTING.value
            elif self.reset_value == RESET_STATUS.RESETTING.value:
                self.reset_value = RESET_STATUS.PURGING.value
            elif self.reset_value == RESET_STATUS.PURGING.value:
                self.reset_value = RESET_STATUS.PURGE_DONE.value
            elif self.reset_value == RESET_STATUS.PURGE_DONE.value:
                self.reset_value = RESET_STATUS.RESET_COMPLETE.value
            else:
                self.reset_requested = 0

        if self.purge_requested:
            if self.reset_value == RESET_STATUS.NOT_RESETTING_OR_PURGING.value:
                self.reset_value = RESET_STATUS.PURGING.value
            elif self.reset_value == RESET_STATUS.PURGING.value:
                self.reset_value = RESET_STATUS.PURGE_DONE.value
            else:
                self.purge_requested = 0

        if self.stop_requested:
            self.stop_bit = 1
            self.run_bit = 0
            self.busy_bit = 0
            self.ramping = 0
            self.stop_requested = 0
        if self.run_requested:
            self.stop_bit = 0
            self.run_bit = 1
            self.busy_bit = 1
            self.ramping = 1
            self.run_requested = 0
        if self.run_bit == 1:
            self.running()
        pressure = self.get_pressure()
        if pressure > self.user_stop_limit:
            self.last_error_code = 12
            self.stop_requested = 1

# need to do closed loop better
    def running(self):
        pressure = self.get_pressure()
        if self.ramping == 1:
            incr = abs(pressure - self.setpoint_value)
            if incr == 0:
                if self.loop_mode == 0:
                    self.stop_requested = 1
                else:
                    self.ramping = 0
            if incr > self.pressure_rate:
                incr = self.pressure_rate
            if pressure < self.setpoint_value:
                self.pump_pressure = self.pump_pressure + incr
                self.cell_pressure = self.pump_pressure  # for simplicity
            else:
                self.pump_pressure = self.pump_pressure - incr
                self.cell_pressure = self.pump_pressure  # for simplicity

        # if self.loop_mode == 1:    maintain between min_value_pre_servoing and max_value_pre_servoing

        if abs(self.cell_pressure - self.pump_pressure) > self.transducer_difference_threshold:
            self.last_error_code = 10
            self.stop_requested = 1

    def set_em_stop_status(self, em_stop_status: int):
        """
        Set emergency stop circuit status.
        1 denotes that the system has stopped. 0 denotes the system is running
        @param em_stop_status: (int) Device status value for requesting emergency stop circuit - range [0-1]
        """
        print(f"Received EM stop circuit status: {em_stop_status}")
        self.em_stop_status = em_stop_status
        self.add_to_dict(value_id="EM", unvalidated_value=self.em_stop_status)

    def set_ru(self, run_bit: int):
        """
        Set Run Bit which denotes is mechanically active
        @param run_bit: (int) Value to start servo loop execution,
        pumping to achieve the setpoint pressure - range [0-1]
        """
        print(f"Received run bit: {run_bit}")
        self.run_bit = run_bit
        self.add_to_dict(value_id="ru", unvalidated_value=self.run_bit)

    def set_re(self, piston_reset_phase: int):
        """
        Set the reset value to represent the 4 stages of resetting the pistons
        @param reset_value: (int) value representing each stage during piston reset - range [0-4]
        """
        print(f"Received reset phase value: {piston_reset_phase}")
        self.reset_value = piston_reset_phase
        self.add_to_dict(
            value_id="re", unvalidated_value=self.piston_reset_phase)

    def set_pu(self, purge_value: int):
        """
        Set the reset value to represent the 2 stages of purging the system
        @param purge_value: (int) value representing each stage during system purge - [2,4]
        """
        print(f"Received purge phase value: {purge_value}")
        self.reset_value = purge_value
        self.add_to_dict(value_id="re", unvalidated_value=self.reset_value)

    def set_stop_bit(self, stop_bit: int):
        """
        Set the stop bit to 1 or 0 where 1 requests the system to stop. This value is
        set automatically at the end of a move or set to stop system manually
        @param stop_bit: (int) status value to stop system at the end of a move or by request - range [0-1]
        """
        print(f"Received stop bit command: {stop_bit}")
        self.stop_bit = stop_bit
        self.add_to_dict(value_id="St", unvalidated_value=self.stop_bit)

    def set_by(self, busy_bit: int):
        """
        Set the busy bit status
        1 denotes that the device is busy and 0 not busy
        @type busy_bit: (int) integer representing if device is mechanically active - range [0-1]
        """
        print(f"Received busy bit {busy_bit}")
        self.busy_bit = busy_bit
        self.add_to_dict(value_id="by", unvalidated_value=self.busy_bit)

    def set_sf_status(self, sf_status: int):
        """
        Set the seal fail bit status
        1 denotes that it has failed, 0 not
        @type sf_bit: (int) integer representing if seal has failed - range [0-1]
        """
        print(f"Received seal fail bit {sf_status}")
        self.seal_fail_status = sf_status
        self.add_to_dict(value_id="sf_status",
                         unvalidated_value=self.seal_fail_status)

    def set_go(self, go_status: int):
        """
        Set GO status to to 1 if system was initiated by host.
        1 - set by host
        0 - not set by host
        @param go_status (int) set if command initiated by host - range [0-1]
        """
        print(f"Received GO status: {go_status}")
        self.go_status = go_status
        self.add_to_dict(value_id="GO", unvalidated_value=self.go_status)

    def set_am(self, am_mode: int):
        """
        Set AM auto/manual switch position mode
        @param am_mode: (int) Set Auto/manual switch position - range [0-1]
        """
        print(f"Received last AM modeL: {am_mode}")
        self.am_mode = am_mode
        self.add_to_dict(value_id="AM", unvalidated_value=self.am_mode)

    def set_er(self, last_error_code: int):
        """
        Set the last error code
        @param last_error_code: (int) Last error status received by device - range [0-19]
        """
        print(f"Received last error code: {last_error_code}")
        self.last_error_code = last_error_code
        self.add_to_dict(value_id="ER", unvalidated_value=self.last_error_code)

    def set_pressures(self, pump_pressure, cell_pressure):
        self.pump_pressure = pump_pressure
        self.cell_pressure = cell_pressure
