import time
import threading
from lewis.devices import StateMachineDevice
from lewis.core import approaches
from .states import DefaultState
from collections import OrderedDict


class SimulatedPearlPC(StateMachineDevice):

    def _initialize_data(self):
        self.re_initialise()

        # When the device is in an error state it can respond with junk
        self.is_giving_errors = False
        self.out_error = "}{<7f>w"
        self.out_terminator_in_error = ""
        t = threading.Thread(target=self.poller)
        t.start()

    def _get_state_handlers(self):
        return {
            'default': DefaultState(),
        }

    def _get_initial_state(self):
        return 'default'

    def _get_transition_handlers(self):
        return OrderedDict([])

    def re_initialise(self):
        self.initial_id_prefix = 1111 # 4 digits
        self.secondary_id_prefix = 1111 # 4 digits
        self.em_stop_status = 0  # Bool [0-1]
        self.run_bit = 0  # Bool [0-1]
        self.reset_value = 0 # [0-4]
        self.piston_reset_phase = 0
        self.stop_bit = 0  # Bool [0-1]
        self.busy_bit = 0  # Bool [0-1]
        self.go_status = 0
        self.am_mode = 1 # auto mode (run from host) rather than manual
        self.loop_mode = 0  # Bool [0-1]
        self.seal_fail_value = 0
        self.seal_fail_status = 0 # set to 1 if sudden pressure drop more than seal_fail_value
        self.last_error_code = 0
        self.pressure_rate = 0
        self.min_value_pre_servoing = 0
        self.setpoint_value = 0
        self.max_value_pre_servoing = 0
        self.inputs = 0 # a 9 digit number like 111111001 showing input status
        self.cell_pressure = 0
        self.pump_pressure = 0
        self.transducer_threashold = 2
        self.algorithm = "a"
        self.transducer = "0"
        self.user_stop_limit = 0
        self.offset_plus = 0
        self.offset_minus = 0
        self.dir_plus = 0
        self.dir_minus = 0

        # for comms with poller thread
        self.run_requested = 0
        self.stop_requested = 0
        self.reset_requested = 0
        self.ramping = 0 # ramping to setpoint as opposed to closed loop stabilisation?

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
            value = weight * self.cell_pressure + (1.0 - weight) * self.pump_pressure
        return int(value)

    def stop(self):
        self.stop_requested = 1
    
    def reset(self):
        self.reset_requested = 1
    
    def run(self):
        self.run_requested = 1
    
    def poller(self):
        while(True):
            self.inputs = int("011110000") + int("000000001") * self.am_mode
            if self.reset_requested:
                if self.reset_value == 0:
                    self.reset_value = 2
                elif self.reset_value == 2:
                    self.reset_value = 4
                elif self.reset_value == 4:
                    self.reset_value = 3
                elif self.reset_value == 3:
                    self.reset_value = 1
                else:
                    self.reset_requested = 0
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
                
            time.sleep(1)

# need to do closed lop better
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
                self.pump_pressure =  pressure + incr
                self.cell_pressure = pressure + incr
            else:
                self.pump_pressure =  pressure - incr
                self.cell_pressure = pressure - incr
        
        # if self.loop_mode == 1:    maintain between min_value_pre_servoing and max_value_pre_servoing             

        if abs(self.cell_pressure - self.pump_pressure) > self.transducer_threashold:
            self.last_error_code = 10
            self.stop_requested = 1
            
            
