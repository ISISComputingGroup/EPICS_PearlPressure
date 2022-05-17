from lewis.adapters.stream import StreamInterface, Cmd
from lewis.utils.command_builder import CmdBuilder
from lewis.core.logging import has_log
from lewis.utils.replies import conditional_reply


@has_log
class PearlPCStreamInterface(StreamInterface):
    commands = {
        # Get status and id prefixes
        CmdBuilder("get_st").escape("st").eos().build(),
        CmdBuilder("get_id_prefix").escape("id").eos().build(),
        # Set ID prefixes
        CmdBuilder("set_si").escape("si").arg("[0-9]{4}", argument_mapping=int).eos().build(),
        CmdBuilder("set_sd").escape("sd").arg("[0-9]{4}", argument_mapping=int).eos().build(),
        # Device Set commands
        CmdBuilder("set_sloop").escape("sloop").arg("[0-1]{1}", argument_mapping=int).eos().build(),
        CmdBuilder("set_sf").escape("sf").arg("[0-9]{4}", argument_mapping=int).eos().build(),
        CmdBuilder("error_reset").escape("er").eos().build(),
        CmdBuilder("set_ra").escape("ra").arg("[0-9]{4}", argument_mapping=int).eos().build(),
        CmdBuilder("set_mn").escape("mn").arg("[0-9]{4}", argument_mapping=int).eos().build(),
        CmdBuilder("set_sp").escape("sp").arg("[0-9]{4}", argument_mapping=int).eos().build(),
        CmdBuilder("set_mx").escape("mx").arg("[0-9]{4}", argument_mapping=int).eos().build(),
        CmdBuilder("reset").escape("reset").eos().build(), 
        CmdBuilder("run").escape("run").eos().build(), 
        CmdBuilder("stop").escape("stop").eos().build(), 
        CmdBuilder("set_t").escape("t").arg("[1-2]0[1-3][0-9]{2}0[1-3]").eos().build(), 
        CmdBuilder("set_th").escape("th").arg("[0-9]{4}", argument_mapping=int).eos().build(),
        CmdBuilder("transducer_reset").escape("tr").eos().build(), 
        CmdBuilder("set_algorithm").escape("a").arg("[a12hlw][0-9]{0,2}").eos().build(),
        CmdBuilder("get_dt").escape("dt").eos().build(),
        CmdBuilder("set_dir_error").escape("d").arg("[+-]").arg("[0-9]{4}", argument_mapping=int).eos().build(),
        CmdBuilder("set_hist_offset").escape("o").arg("[+-]").arg("[0-9]", argument_mapping=int).eos().build(),
        CmdBuilder("set_user_stop_limit").escape("ul").arg("[0-9]{4}", argument_mapping=int).eos().build(),
        CmdBuilder("show_limits").escape("ls").eos().build(),
        CmdBuilder("get_memory").escape("vr").arg("[0-9]{4}", argument_mapping=int).eos().build(),
        
## these are not real device commands and ideally
## should be accessed via lewis backdoor and not command interface
        CmdBuilder("set_em_stop_status").escape("Em").arg("[0-1]").eos().build(),
        CmdBuilder("set_ru").escape("Ru").arg("[0-1]{1}").eos().build(),
        CmdBuilder("set_re").escape("Re").arg("[0-4]{1}").eos().build(),
        CmdBuilder("set_stop_bit").escape("St").arg("[0-1]{1}").eos().build(),
        CmdBuilder("set_by").escape("By").arg("[0-1]{1}").eos().build(),
        CmdBuilder("set_go").escape("GO").arg("[0-1]{1}").eos().build(),
        CmdBuilder("set_am").escape("AM").arg("[0-1]{1}").eos().build(),
        CmdBuilder("set_er").escape("Er").arg("[0-9]{1,2}").eos().build(),

    }

    in_terminator = "\r"
    out_terminator = "\r\n"

    def __init__(self, status_dictionary=None):
        super().__init__()
        if status_dictionary is None:
            status_dictionary = {}
        self.status_dictionary = status_dictionary

    def add_to_dict(self, value_id: str, unvalidated_value: object):
        """
        Add device state parameters to a dictionary.
        @param value_id: (str) dictionary key for each device parameter
        @param unvalidated_value: (object) device parameter set to describe system status
        """
        self.status_dictionary[value_id] = unvalidated_value

    def get_st(self):
        """
        Get the device status on request
        @return: (str) A formatted string containing all set device parameters describing current device status.
        """
        self._device.poller()
        return f"Status Report{self.out_terminator}" \
               f"Em Ru Re St By Go AM sl sf Er   ra    mn    sp    mx  Press    Inputs{self.out_terminator}" \
               f"{self._device.em_stop_status} " \
               f"{self._device.run_bit} " \
               f"{self._device.reset_value} " \
               f"{self._device.stop_bit} " \
               f"{self._device.busy_bit} " \
               f"{self._device.go_status} " \
               f"{self._device.am_mode} " \
               f"{self._device.loop_mode} " \
               f"{self._device.seal_fail_status} " \
               f"{self._device.last_error_code} " \
               f"{self._device.pressure_rate} " \
               f"{self._device.min_value_pre_servoing} " \
               f"{self._device.setpoint_value} " \
               f"{self._device.max_value_pre_servoing} " \
               f"{self._device.get_pressure()} " \
               f"{self._device.inputs:09d}{self.out_terminator}" \
               f"OK"               

    def get_id_prefix(self):
        """
        Returns ID prefixes (first 2 numbers selectable by the user formatted as: "<IDP_1> <IDP_2>")
        @return: (str) formatted string returning ID prefixes set by default or by user.
        """
        print(f"ID prefix set to: {self._device.initial_id_prefix} {self._device.secondary_id_prefix}")
        return f"{self._device.initial_id_prefix:04d} {self._device.secondary_id_prefix:04d} ISIS PEARL pressure intensifier V2.3"

    def set_si(self, id_prefix: int):
        """
        Set initial ID Prefix. ID should form a unique number for each unit.
        The ID allows for communication with each associated unit.
        @param id_prefix: (int) Prefix to ID for a unit - range [0000-9999]
        """
        print(f"SI prefix value received: {id_prefix}")
        if (id_prefix < 0 or id_prefix > 9999):
            print("ERROR: invalid si value")

        self._device.initial_id_prefix = id_prefix
        self.add_to_dict(value_id="si", unvalidated_value=self._device.initial_id_prefix)
        return ""
    
    def set_sd(self, secondary_id_prefix: int):
        """
        Set Secondary ID Prefix. ID should form a unique number for each unit.
        ID allows for communication with each associated unit.
        Secondary ID prefix is usually set to be the same at initial ID prefix
        @param secondary_id_prefix: (int) Prefix to ID for a unit - range [0000-9999]
        """
        print(f"SD prefix value received: {secondary_id_prefix}")
        if (secondary_id_prefix < 0 or secondary_id_prefix > 9999):
            print("ERROR: invalid sd value")
        self._device.secondary_id_prefix = secondary_id_prefix
        self.add_to_dict(value_id="sd", unvalidated_value=self._device.secondary_id_prefix)
        return ""

    def set_em_stop_status(self, em_stop_status: int):
        """
        Set emergency stop circuit status.
        1 denotes that the system has stopped. 0 denotes the system is running
        @param em_stop_status: (int) Device status value for requesting emergency stop circuit - range [0-1]
        """
        print(f"Received EM stop circuit status: {em_stop_status}")
        self._device.em_stop_status = em_stop_status
        self.add_to_dict(value_id="EM", unvalidated_value=self._device.em_stop_status)

    def set_ru(self, run_bit: int):
        """
        Set Run Bit which denotes is mechanically active
        @param run_bit: (int) Value to start servo loop execution,
        pumping to achieve the setpoint pressure - range [0-1]
        """
        print(f"Received run bit: {run_bit}")
        self._device.run_bit = run_bit
        self.add_to_dict(value_id="ru", unvalidated_value=self._device.run_bit)

    def set_re(self, piston_reset_phase: int):
        """
        Set the reset value to represent the 4 stages of resetting the pistons
        @param reset_value: (int) value representing each stage during piston reset - range [0-4]
        """
        print(f"Received reset phase value: {piston_reset_phase}")
        self._device.reset_value = piston_reset_phase
        self.add_to_dict(value_id="re", unvalidated_value=self._device.piston_reset_phase)

    def reset(self):
        """
        Reset to fully open pistons
        """
        if self._device.get_pressure() < 100:
            print(f"starting reset")
            self._device.reset() # set phase to resetting, this starts reset
        else:
            print("ERROR: cannot reset as pressure too high")
            self._device.last_error_code = 1
        return ""
    
    def set_stop_bit(self, stop_bit: int):
        """
        Set the stop bit to 1 or 0 where 1 requests the system to stop. This value is 
        set automatically at the end of a move or set to stop system manually
        @param stop_bit: (int) status value to stop system at the end of a move or by request - range [0-1]
        """
        print(f"Received stop bit command: {stop_bit}")
        self._device.stop_bit = stop_bit
        self.add_to_dict(value_id="St", unvalidated_value=self._device.stop_bit)

    def set_by(self, busy_bit: int):
        """
        Set the busy bit status
        1 denotes that the device is busy and 0 not busy
        @type busy_bit: (int) integer representing if device is mechanically active - range [0-1]
        """
        print(f"Received busy bit {busy_bit}")
        self._device.busy_bit = busy_bit
        self.add_to_dict(value_id="by", unvalidated_value=self._device.busy_bit)

    def set_go(self, go_status: int):
        """
        Set GO status to to 1 if system was initiated by host.
        1 - set by host
        0 - not set by host
        @param go_status (int) set if command initiated by host - range [0-1]
        """
        print(f"Received GO status: {go_status}")
        self._device.go_status = go_status
        self.add_to_dict(value_id="GO", unvalidated_value=self._device.go_status)

    def set_am(self, am_mode: int):
        """
        Set AM auto/manual switch position mode
        @param am_mode: (int) Set Auto/manual switch position - range [0-1]
        """
        print(f"Received last AM modeL: {am_mode}")
        self._device.am_mode = am_mode
        self.add_to_dict(value_id="AM", unvalidated_value=self._device.am_mode)

    def set_sloop(self, sloop: int):
        """
        Represents binary bit to set loop mode
        0 = open loop mode
        1 = close loop mode
        Open loop mode ramps to pressure in control system and then stop until anther command is sent.
        Close loop mode will ramp to setpoint pressure value and remain active monitoring delivered pressure, 
        acting on mn and mx pressure values.
        @param sloop: (int) integer value setting system to open or closed loop - range [0-1]
        """
        print(f"sloop value recieved: {sloop}")
        if (sloop < 0 or sloop > 1):
            print("ERROR: invalid sloop")
        self._device.loop_mode = sloop
        self.add_to_dict(value_id="sloop", unvalidated_value=self._device.loop_mode)
        return ""

    def set_sf(self, seal_fail_value: int):
        """
        Set Seal Fail drop value.
        Sets the pressure drop required to trigger Seal Fail mode.
        @param seal_fail_value: (int) Seal Fail Mode Trigger Value - range [0001-0999]
        """
        print(f"Seal Fail mode trigger value received: {seal_fail_value}")
        if (seal_fail_value < 1 or seal_fail_value > 999):
           print("ERROR: invalid seal fail value")
        self._device.seal_fail_value = seal_fail_value
        self.add_to_dict(value_id="sf", unvalidated_value=self._device.seal_fail_value)
        return ""

    def set_er(self, last_error_code: int):
        """
        Set the last error code
        @param last_error_code: (int) Last error status received by device - range [0-19]
        """
        print(f"Received last error code: {last_error_code}")
        self._device.last_error_code = last_error_code
        self.add_to_dict(value_id="ER", unvalidated_value=self._device.last_error_code)

    def error_reset(self):
        """
        reset the last error code execpt for code 8 (seal fail)
        """
        if (self._device.last_error_code != 8):
            self._device.last_error_code = 0
            print(f"Resetting last error code: {self._device.last_error_code}")
        else:
            print("ERROR: Cannot reset seal fail")
        return f"Resetting error {self._device.last_error_code}"

    def set_ra(self, pressure_rate: int):
        """
        Set rate of pressure application in Bar/min
        A value of 0000 will be used to represent maximum slew rate of the motor.
        Normally set to 0010
        @param pressure_rate: (int) Pressure rate within range [0001-0040]
        """
        print(f"Pressure Rate Received: {pressure_rate}")
        if (pressure_rate < 0 or pressure_rate > 40):
            print("ERROR: invalid pressure rate")
        if (pressure_rate == 0):
            self._device.pressure_rate = 10 # maximum slew rate of the motor?
        else:            
            self._device.pressure_rate = pressure_rate
        self.add_to_dict(value_id="ra", unvalidated_value=self._device.pressure_rate)
        return ""

    def set_mn(self, min_measured: int):
        """
        Set the minimum value before re-servoing.
        This will only be acted upon in closed loop mode.
        @param min_measured: (int) minimum pressure value before re-servoing - range [0001-9999]
        """
        if (min_measured < 1 or min_measured > 9999):
            print("ERROR: invalid min measured")
        print(f"Minimum value before re-servoing received: {min_measured}")
        self._device.min_value_pre_servoing = min_measured
        self.add_to_dict(value_id="mn", unvalidated_value=self._device.min_value_pre_servoing)
        return ""

    def set_sp(self, setpoint: int):
        """
        Set a setpoint to be initially reached if the measured pressure exceeds maximum value (mx)
        or falls below minimum value (mn) and the servo loop is closed.
        The motor will operate until the pressure is restored to the setpoint value
        @param setpoint: (int) Set Point trigger value - range [0001-1000]
        """
        print(f"Setpoint value received: {setpoint}")
        if (setpoint < 1 or setpoint > 1000):
            print("ERROR: invalid setpoint")
        self._device.setpoint_value = setpoint
        self.add_to_dict(value_id="sp", unvalidated_value=self._device.setpoint_value)
        return ""

    def set_mx(self, max_measured: int):
        """
        set the maximum measured value before re-servoing
        @param max_measured: (integer) maximum measured value before re-servoing - range [0001-9999]
        """
        if (max_measured < 1 or max_measured > 9999):
            print("ERROR: invalid max measured")
        print(f"Maximum measured value before re-servoing received: {max_measured}")
        self._device.max_value_pre_servoing = max_measured
        self.add_to_dict(value_id="mx", unvalidated_value=self._device.max_value_pre_servoing)
        return ""

    def handle_error(self, request:object, error:object):
        """
        Return any errors which have occurred when sending requests to device.
        @return: (str) Formatted error message
        """
        print(f"An error occurred at request {repr(request)} : {repr(error)}")

    def run(self):
        print("run")
        self._device.run()
        return ""
    
    def stop(self):
        print("stop")
        self._device.stop()
        return ""

    def set_t(self, value):
        print(f"set_transducer  {value}")
        self._device.transducer = value
        return ""

    def set_th(self, value: int):
        print(f"set_transducer threshold {value}")
        if (value < 1 or value > 999):
            print("ERROR: invalid th value")
        self._device.transducer_threashold = value
        return ""

    def transducer_reset(self):
        print("transducer_reset")
        return ""

    def set_algorithm(self, value):
        print(f"set_algorithm {value}")
        self._device.algorithm = value
        return ""

    def get_dt(self):
        print("get_dt")
        return "Transducer settings"

    def set_dir_error(self, dir, value : int):
        print(f"set_dir_error {dir}{value}")
        if dir == "+":
            self._device.dir_plus = value
        elif dir == "-":
            self._device.dir_minus = value
        else:
            print(f"ERROR: set_dir_error {dir}{value}")
        
        return ""

    def set_hist_offset(self, dir, value : int):
        print(f"set_hist_offset {dir}{value}")
        if dir == "+":
            self._device.offset_plus = value
        elif dir == "-":
            self._device.offset_minus = value
        else:
            print(f"ERROR: set_hist_offset {dir}{value}")
        return ""

    def set_user_stop_limit(self, value: int):
        print(f"set_user_stop_limit {value}")
        if value < 0 or value > 9999:
            print("ERROR: set_user_stop_limit")
        self._device.user_stop_limit = value
        return ""

    def show_limits(self):
        print("show_limits")
        return f"User +Change +Offset -Change -Offset{self.out_terminator}" \
               f"{self._device.user_stop_limit} {self._device.dir_plus} {self._device.offset_plus} {self._device.dir_minus} {self._device.offset_minus}{self.out_terminator}" \
               f"OK"
        
    def get_memory(self, address: int):
        value = 0
        if (address < 0 or address > 1023):
            print("ERROR: show memory address")
        elif (address == 2): # error number
            value = self._device.last_error_code
        elif (address == 81): # pressure difference set by th command
            value = self._device.transducer_threashold
        elif (address == 82): # pressure difference between transducers
            value = self._device.cell_pressure - self._device.pump_pressure
        elif (address == 83): # cell status, 0 = working
            value = 0
        elif (address == 84): # pump status, 0 = working
            value = 0
        elif (address == 85): # pressure algorithm
            value = ord(self._device.algorithm[0])
        elif (address == 87): # Sensor 1 (cell) measured pressure
            value = self._device.cell_pressure
        elif (address == 88): # Sensor 2 (pump) measured pressure
            value = self._device.pump_pressure
        elif (address == 126): # seal fail limit 
            value = self._device.seal_fail_value
        else:
            print(f"ERROR: read memory error address {address}")
        return f"vr{address:04d} {value}"

    