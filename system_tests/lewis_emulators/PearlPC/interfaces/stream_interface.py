from lewis.adapters.stream import StreamInterface
from lewis.core.logging import has_log
from lewis.utils.command_builder import CmdBuilder
from lewis.utils.replies import conditional_reply


@has_log
class PearlPCStreamInterface(StreamInterface):
    commands = {
        # Get status and id prefixes
        CmdBuilder("get_st").escape("st").eos().build(),
        # ID deliberately does not append .eos() as it uses weird terminators
        CmdBuilder("get_id").escape("id").build(),
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
        CmdBuilder("purge").escape("pu").eos().build(),
        CmdBuilder("run").escape("run").eos().build(),
        CmdBuilder("stop").escape("stop").eos().build(),
        CmdBuilder("set_t").escape("t").arg("[1-2]0[1-3][0-9]{2}0[1-3]").eos().build(),
        CmdBuilder("set_th").escape("th").arg("[0-9]{4}", argument_mapping=int).eos().build(),
        CmdBuilder("transducer_reset").escape("tr").eos().build(),
        CmdBuilder("set_algorithm").escape("a").arg("[a12hlw][0-9]{0,2}").eos().build(),
        CmdBuilder("get_dt").escape("dt").eos().build(),
        CmdBuilder("set_user_stop_limit")
        .escape("ul")
        .arg("[0-9]{4}", argument_mapping=int)
        .eos()
        .build(),
        CmdBuilder("show_limits").escape("ls").eos().build(),
        CmdBuilder("get_memory").escape("vr").arg("[0-9]{4}", argument_mapping=int).eos().build(),
        CmdBuilder("set_pos_lim").escape("d+").arg("[0-9]{4}", argument_mapping=int).eos().build(),
        CmdBuilder("set_neg_lim").escape("d-").arg("[0-9]{4}", argument_mapping=int).eos().build(),
        CmdBuilder("set_pos_offset")
        .escape("o+")
        .arg("[0-9]{1}", argument_mapping=int)
        .eos()
        .build(),
        CmdBuilder("set_neg_offset")
        .escape("o-")
        .arg("[0-9]{1}", argument_mapping=int)
        .eos()
        .build(),
    }

    in_terminator = "\r"
    out_terminator = "\r\n"

    def __init__(self) -> None:
        super().__init__()

    @conditional_reply("connected")
    def get_st(self) -> str:
        """
        Get the device status on request
        @return: (str) A formatted string containing all
        set device parameters describing current device status.
        """
        self._device.poller()
        return (
            f"Status Report{self.out_terminator}"
            f"Em Ru Re St By Go AM sl sf Er   ra    mn    sp    mx  Press    Inputs{self.out_terminator}"  # noqa: E501
            f"{self._device.em_stop_status} "
            f"{self._device.run_bit} "
            f"{self._device.reset_value} "
            f"{self._device.stop_bit} "
            f"{self._device.busy_bit} "
            f"{self._device.go_status} "
            f"{self._device.am_mode} "
            f"{self._device.loop_mode} "
            f"{self._device.seal_fail_status} "
            f"{self._device.last_error_code} "
            f"{self._device.pressure_rate} "
            f"{self._device.min_value_pre_servoing} "
            f"{self._device.setpoint_value} "
            f"{self._device.max_value_pre_servoing} "
            f"{self._device.get_pressure()} "
            f"{self._device.inputs:09d}{self.out_terminator}"
            f"OK"
        )

    @conditional_reply("connected")
    def get_id(self) -> str:
        """
        Returns ID
        @return: (str) formatted string returning ID prefixes set by default or by user.
        """
        print(
            f"ID prefix set to: {self._device.initial_id_prefix} {self._device.secondary_id_prefix}"
        )

        return f"\r\n{self._device.initial_id_prefix:04d} {self._device.secondary_id_prefix:04d} ISIS PEARL INTENSIFIER CONTROLLER V2.4 {self._device.fluid_type}\r\n\n"  # noqa: E501

    @conditional_reply("connected")
    def set_fluid_type(self, fluid_type: int) -> None:
        self._device.set_fluid_type(fluid_type)
        print("Fluid type set to: " + self._device.fluid_type)

    @conditional_reply("connected")
    def set_si(self, id_prefix: int) -> str:
        """
        Set initial ID Prefix. ID should form a unique number for each unit.
        The ID allows for communication with each associated unit.
        @param id_prefix: (int) Prefix to ID for a unit - range [0000-9999]
        """
        print(f"SI prefix value received: {id_prefix}")
        if id_prefix < 0 or id_prefix > 9999:
            print("ERROR: invalid si value")

        self._device.initial_id_prefix = id_prefix
        self._device.add_to_dict(value_id="si", unvalidated_value=self._device.initial_id_prefix)
        return ""

    @conditional_reply("connected")
    def set_sd(self, secondary_id_prefix: int) -> str:
        """
        Set Secondary ID Prefix. ID should form a unique number for each unit.
        ID allows for communication with each associated unit.
        Secondary ID prefix is usually set to be the same at initial ID prefix
        @param secondary_id_prefix: (int) Prefix to ID for a unit - range [0000-9999]
        """
        print(f"SD prefix value received: {secondary_id_prefix}")
        if secondary_id_prefix < 0 or secondary_id_prefix > 9999:
            print("ERROR: invalid sd value")
        self._device.secondary_id_prefix = secondary_id_prefix
        self._device.add_to_dict(value_id="sd", unvalidated_value=self._device.secondary_id_prefix)
        return ""

    @conditional_reply("connected")
    def reset(self) -> str:
        """
        Reset to fully open pistons
        """
        if self._device.get_pressure() < 100:
            print("starting reset")
            self._device.reset()  # set phase to resetting, this starts reset
        else:
            print("ERROR: cannot reset as pressure too high")
            self._device.last_error_code = 1
        return ""

    @conditional_reply("connected")
    def purge(self) -> str:
        """
        Reset to fully open pistons
        """
        if self._device.get_pressure() < 100:
            print("starting purge")
            self._device.purge()  # set phase to purging, this starts purge
        else:
            print("ERROR: cannot purge as pressure too high")
            self._device.last_error_code = 1
        return ""

    @conditional_reply("connected")
    def set_sloop(self, sloop: int) -> str:
        """
        Represents binary bit to set loop mode
        0 = open loop mode
        1 = close loop mode
        Open loop mode ramps to pressure in control system and then stop til anther command is sent.
        Close loop mode will ramp to setpoint pressure value and
        remain active monitoring delivered pressure,
        acting on mn and mx pressure values.
        @param sloop: (int) integer value setting system to open or closed loop - range [0-1]
        """
        print(f"sloop value recieved: {sloop}")
        if sloop < 0 or sloop > 1:
            print("ERROR: invalid sloop")
        self._device.loop_mode = sloop
        self._device.add_to_dict(value_id="sloop", unvalidated_value=self._device.loop_mode)
        return ""

    @conditional_reply("connected")
    def set_sf(self, seal_fail_value: int) -> str:
        """
        Set Seal Fail drop value.
        Sets the pressure drop required to trigger Seal Fail mode.
        @param seal_fail_value: (int) Seal Fail Mode Trigger Value - range [0001-0999]
        """
        print(f"Seal Fail mode trigger value received: {seal_fail_value}")
        if seal_fail_value < 1 or seal_fail_value > 999:
            print("ERROR: invalid seal fail value")
        self._device.seal_fail_value = seal_fail_value
        self._device.add_to_dict(value_id="sf", unvalidated_value=self._device.seal_fail_value)
        return ""

    @conditional_reply("connected")
    def error_reset(self) -> str:
        """
        reset the last error code execpt for code 8 (seal fail)
        """
        if self._device.last_error_code != 8:
            self._device.last_error_code = 0
            print(f"Resetting last error code: {self._device.last_error_code}")
        else:
            print("ERROR: Cannot reset seal fail")
        return f"Resetting error {self._device.last_error_code}"

    @conditional_reply("connected")
    def set_ra(self, pressure_rate: int) -> str:
        """
        Set rate of pressure application in Bar/min
        A value of 0000 will be used to represent maximum slew rate of the motor.
        Normally set to 0010
        @param pressure_rate: (int) Pressure rate within range [0001-0040]
        """
        print(f"Pressure Rate Received: {pressure_rate}")
        if pressure_rate < 0 or pressure_rate > 40:
            print("ERROR: invalid pressure rate")
        if pressure_rate == 0:
            self._device.pressure_rate = 10  # maximum slew rate of the motor?
        else:
            self._device.pressure_rate = pressure_rate
        self._device.add_to_dict(value_id="ra", unvalidated_value=self._device.pressure_rate)
        return ""

    @conditional_reply("connected")
    def set_mn(self, min_measured: int) -> str:
        """
        Set the minimum value before re-servoing.
        This will only be acted upon in closed loop mode.
        @param min_measured: (int) minimum pressure value before re-servoing - range [0001-9999]
        """
        if min_measured < 1 or min_measured > 9999:
            print("ERROR: invalid min measured")
        print(f"Minimum value before re-servoing received: {min_measured}")
        self._device.min_value_pre_servoing = min_measured
        self._device.add_to_dict(
            value_id="mn", unvalidated_value=self._device.min_value_pre_servoing
        )
        return ""

    @conditional_reply("connected")
    def set_sp(self, setpoint: int) -> str:
        """
        Set a setpoint to be initially reached if the measured pressure exceeds maximum value (mx)
        or falls below minimum value (mn) and the servo loop is closed.
        The motor will operate until the pressure is restored to the setpoint value
        @param setpoint: (int) Set Point trigger value - range [0001-1000]
        """
        print(f"Setpoint value received: {setpoint}")
        if setpoint < 1 or setpoint > 1000:
            print("ERROR: invalid setpoint")
        self._device.setpoint_value = setpoint
        self._device.add_to_dict(value_id="sp", unvalidated_value=self._device.setpoint_value)
        return ""

    @conditional_reply("connected")
    def set_mx(self, max_measured: int) -> str:
        """
        set the maximum measured value before re-servoing
        @param max_measured: (integer) maximum measured value before re-servoing - range [0001-9999]
        """
        if max_measured < 1 or max_measured > 9999:
            print("ERROR: invalid max measured")
        print(f"Maximum measured value before re-servoing received: {max_measured}")
        self._device.max_value_pre_servoing = max_measured
        self._device.add_to_dict(
            value_id="mx", unvalidated_value=self._device.max_value_pre_servoing
        )
        return ""

    def handle_error(self, request: object, error: object) -> None:
        """
        Return any errors which have occurred when sending requests to device.
        @return: (str) Formatted error message
        """
        print(f"An error occurred at request {repr(request)} : {repr(error)}")

    @conditional_reply("connected")
    def run(self) -> str:
        print("run")
        self._device.run()
        return ""

    @conditional_reply("connected")
    def stop(self) -> str:
        print("stop")
        self._device.stop()
        return ""

    @conditional_reply("connected")
    def set_t(self, value: int) -> str:
        print(f"set_transducer  {value}")
        self._device.transducer = value
        return ""

    @conditional_reply("connected")
    def set_th(self, value: int) -> str:
        print(f"set_transducer threshold {value}")
        if value < 1 or value > 999:
            print("ERROR: invalid th value")
        self._device.transducer_difference_threshold = value
        return ""

    @conditional_reply("connected")
    def transducer_reset(self) -> str:
        print("transducer_reset")
        return ""

    @conditional_reply("connected")
    def set_algorithm(self, value: str) -> str:
        print(f"set_algorithm {value}")
        self._device.algorithm = value
        return ""

    @conditional_reply("connected")
    def get_dt(self) -> str:
        print("get_dt")
        return "Transducer settings"

    @conditional_reply("connected")
    def set_user_stop_limit(self, value: int) -> str:
        print(f"set_user_stop_limit {value}")
        if value < 0 or value > 9999:
            print("ERROR: set_user_stop_limit")
        self._device.user_stop_limit = value
        return ""

    @conditional_reply("connected")
    def show_limits(self) -> str:
        print("show_limits")
        return (
            f"User +Change +Offset -Change -Offset{self.out_terminator}"
            f"{self._device.user_stop_limit} {self._device.dir_plus} {self._device.offset_plus} {self._device.dir_minus} {self._device.offset_minus}{self.out_terminator}"  # noqa: E501
            f"OK"
        )

    @conditional_reply("connected")
    def get_memory(self, address: int) -> str:
        value = 0
        if address < 0 or address > 1023:
            print("ERROR: show memory address")
        elif address == 2:  # error number
            value = self._device.last_error_code
        elif address == 81:  # pressure difference set by th command
            value = self._device.transducer_difference_threshold
        elif address == 82:  # pressure difference between transducers
            value = self._device.cell_pressure - self._device.pump_pressure
        elif address == 83:  # cell status, 0 = working
            value = 0
        elif address == 84:  # pump status, 0 = working
            value = 0
        elif address == 85:  # pressure algorithm
            value = ord(self._device.algorithm[0])
        elif address == 87:  # Sensor 1 (cell) measured pressure
            value = self._device.cell_pressure
        elif address == 88:  # Sensor 2 (pump) measured pressure
            value = self._device.pump_pressure
        elif address == 126:  # seal fail limit
            value = self._device.seal_fail_value
        else:
            print(f"ERROR: read memory error address {address}")
        return f"vr{address:04d} {value}"

    def set_pos_lim(self, value: str) -> str:
        self._device.dir_plus = value
        return ""

    def set_neg_lim(self, value: str) -> str:
        self._device.dir_minus = value
        return ""

    def set_pos_offset(self, value: str) -> str:
        self._device.offset_plus = value
        return ""

    def set_neg_offset(self, value: str) -> str:
        self._device.offset_minus = value
        return ""
