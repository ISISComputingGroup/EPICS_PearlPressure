import itertools
import unittest

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.testing import get_running_lewis_and_ioc, assert_log_messages, skip_if_recsim, parameterized_list
from parameterized import parameterized

# Device prefix
DEVICE_A_PREFIX = "PEARLPC_01"

EMULATOR_DEVICE = "PearlPC"

IOCS = [
    {
        "name": DEVICE_A_PREFIX,
        "directory": get_default_ioc_dir("PEARLPC"),
        "emulator": EMULATOR_DEVICE,
        "emulator_id": DEVICE_A_PREFIX,
    },
]

TEST_MODES = [TestModes.DEVSIM]


INPUT_PVS = [
    "INPUTS:EM_STOP_RELEASED",
    "INPUTS:CYL_B_LOWLIM",
    "INPUTS:CYL_B_UPLIM",
    "INPUTS:CYL_A_LOWLIM",
    "INPUTS:CYL_A_UPLIM",
    "INPUTS:PUMP_B_SEL",
    "INPUTS:INC_PRESSED",
    "INPUTS:DEC_PRESSED",
    "INPUTS:AUTO",
]

LIMIT_PVS = [
    "USER_LIMIT",
    "LIMITS:POS_CHANGE",
    "LIMITS:POS_OFFSET",
    "LIMITS:NEG_CHANGE",
    "LIMITS:NEG_OFFSET",
]

ERRORS = [
    (0, "no error"),
    (1, "Pressure above safe reset level"),
    (2, "\\"),
    (3, ">"),
    (4, "/"),
    (5, "non numeric char from host PC"),
    (6, "EMERGENCY STOPPED"),
    (7, "Motors at limits"),
    (8, "Seal Failure"),
    (9, "Transducer Configuration Error"),
    (10, "Transducers diff > threshold"),
    (11, "Transducer problem"),
    (12, "Pressure above user limit"),
    (13, "Pressure incr should be decr"),
    (14, "Pressure decr should be incr"),
    (15, "READ_2_PRESSURE process stopped"),
    (16, "MOTOR process has stopped"),
    (17, "DISPLAY process has stopped"),
    (18, "PEARL_FG process has stopped"),
    (19, "MONITOR process has stopped"),
]

# List of PVs that are locked when dae is not in setup (is in some form of running state)
# or when not in manager mode
PVS_LOCKED = [
    "PRESSURE:SP",
    "SEND_PARAMETERS",
    "RESET:SP",
    "STOP:SP",
    "RUN:SP",

    "USER_LIMIT:SP",
    "LIMITS:POS_CHANGE:SP",
    "LIMITS:POS_OFFSET:SP",
    "LIMITS:NEG_CHANGE:SP",
    "LIMITS:NEG_OFFSET:SP",
    "PRESSURE_DIFF_THOLD:SP",
]

class PEARLPCTests(unittest.TestCase):
    """
    General Unit tests for the PEARLPC_01.
    """

    def setUp(self):
        self.pressure_value = 35
        self.set_loop_status = 1
        self.default_initial_value = 0
        self.default_id_prefix = 1111
        self.low_pressure = 50
        self.lewis, self.ioc = get_running_lewis_and_ioc(DEVICE_A_PREFIX, DEVICE_A_PREFIX)
        self.ca = ChannelAccess(default_timeout=20, default_wait_time=0.0, device_prefix=DEVICE_A_PREFIX)
        self.lewis.backdoor_run_function_on_device("re_initialise")
        self.reset_dae_run_state_and_manager_mode()
        self.ca.set_pv_value("MN_PRESSURE:SP", 10)
        self.ca.set_pv_value("MX_PRESSURE:SP", 100)
        self.ca.set_pv_value("PRESSURE:SP", 40)

    def reset_dae_run_state_and_manager_mode(self):
        # set DAE state to enable writes to potentially locked PVs
        self.ca.set_pv_value("DAE:RUNSTATE", "SETUP", prefix=self.ca.host_prefix, wait=True)

    @parameterized.expand([
        (True, "set_em_stop_status", 0, 1, 1),
        (True, "set_ru", 1, 1, 1),
        (True, "set_re", 2, 1, 1),
        (True, "set_stop_bit", 3, 1, 1),
        (True, "set_by", 4, 1, 1),
        (True, "set_go", 5, 1, 1),
        (True, "set_am", 6, 1, 1),
        (False, "SERVO", 7, "Closed Loop", 1),
        (True, "set_sf_status", 8, 1, 1),        
        (True, "set_er", 9, 1, 1),
        (False, "PRESSURE_RATE", 10, 35, 35),
        (False, "MN_PRESSURE", 11, 36, 36),
        (False, "MX_PRESSURE", 13, 48, 48)
    ])
    def test_WHEN_pv_set_THEN_pv_and_buffer_readback_correctly(self, emulator_backdoor, target, buffer_location,
                                                               setpoint_value, buffer_value):
        # If true, target is the backdoor function. If false its a pv record
        if emulator_backdoor:
            self.lewis.backdoor_run_function_on_device(target, [setpoint_value])
        else:
            self.ca.set_pv_value("{}:SP".format(target), setpoint_value)
            self.ca.process_pv("SEND_PARAMETERS")
            self.ca.assert_that_pv_is(target, setpoint_value)
        self.ca.assert_that_pv_is("STATUS_ARRAY.[{}]".format(buffer_location), buffer_value)

    # pressure needs to be handled separately to above
    def test_WHEN_pv_set_THEN_pv_and_buffer_readback_correctly_pressure(self):
        self.ca.set_pv_value("PRESSURE:SP", 35)
        self.ca.process_pv("SEND_PARAMETERS")
        self.ca.assert_that_pv_is("PRESSURE:SP:RBV", 35)
        self.ca.assert_that_pv_is("STATUS_ARRAY.[12]", 35)

    def test_WHEN_initial_ID_prefix_set_THEN_initial_ID_prefix_read_back_correctly(self):
        self.ca.set_pv_value("ID_I:SP", self.pressure_value)
        self.ca.assert_that_pv_is("ID_I:SP", self.pressure_value)

    def test_WHEN_secondary_ID_prefix_set_THEN_secondary_ID_prefix_read_back_correctly(self):
        self.ca.set_pv_value("ID_D:SP", self.pressure_value)
        self.ca.assert_that_pv_is("ID_D:SP", self.pressure_value)

    def test_WHEN_id_prefixes_not_set_THEN_default_id_prefixes_read_back_correctly(self):
        self.ca.assert_that_pv_is("ID", f"{self.default_id_prefix} {self.default_id_prefix}")

    def test_WHEN_id_prefixes_set_THEN_id_prefixes_read_back_correctly(self):
        self.ca.set_pv_value("ID_I:SP", self.pressure_value)
        self.ca.set_pv_value("ID_D:SP", self.pressure_value)
        self.ca.assert_that_pv_is("ID", f"{self.pressure_value:04d} {self.pressure_value:04d}")

    def test_WHEN_pressure_set_lower_than_drvl_field_THEN_read_back_correctly(self):
        self.ca.set_pv_value("MN_PRESSURE:SP", 10)
        self.ca.set_pv_value("PRESSURE:SP", 5)
        self.ca.assert_that_pv_is("SEND_PARAMETERS.DISP", "1")

    def test_WHEN_pressure_set_higher_than_drvh_field_THEN_read_back_correctly(self):
        self.ca.set_pv_value("MX_PRESSURE:SP", 60)
        self.ca.set_pv_value("PRESSURE:SP", 80)
        self.ca.assert_that_pv_is("SEND_PARAMETERS.DISP", "1")

    def test_WHEN_reset_bit_value_set_THEN_reset_bit_value_read_back_correctly_HIGH_PRESSURE(self):
        self.ca.set_pv_value("PRESSURE:SP", 35)
        self.ca.process_pv("SEND_PARAMETERS")
        self.ca.assert_that_pv_is("PRESSURE:SP:RBV", 35)
        self.ca.set_pv_value("RESET:SP", 1)
        self.ca.assert_that_pv_is("RESET_STATUS", 1)

    def test_WHEN_General_error_occurs_THEN_general_error_readback_correctly(self):
        self.ca.assert_that_pv_is("GENERAL_ERROR", "NO")
        self.lewis.backdoor_run_function_on_device("set_er", [1])
        self.ca.assert_that_pv_is("GENERAL_ERROR", "YES")

    @parameterized.expand(parameterized_list(ERRORS))
    def test_WHEN_error_occurs_THEN_error_translated_correctly(self, _, code, error):
        self.lewis.backdoor_run_function_on_device("set_er", [code])
        self.ca.assert_that_pv_is("ERRCODE", code)
        self.ca.assert_that_pv_is("LAST_ERR", error, timeout=1)  # Shouldn't be significant delay after previous assert

    def test_WHEN_value_set_THEN_status_readback_correctly(self):
        self.ca.set_pv_value("PRESSURE_RATE:SP", 35)
        self.ca.process_pv("SEND_PARAMETERS")
        self.ca.assert_that_pv_is("PRESSURE_RATE", 35)

    def test_WHEN_correct_conditions_met_THEN_device_ready_state_readback_correctly(self):
        self.ca.assert_that_pv_is("READY_STATE", "READY")

    def test_WHEN_conditions_are_not_met_THEN_device_ready_state_readback_correctly(self):
        self.ca.set_pv_value("RESET:SP", 1)
        self.ca.assert_that_pv_is("READY_STATE", "NOT READY")

    def start_device_with_parameters(self, min_pres, max_pres, nominal_pres, pres_rate):
        self.ca.set_pv_value("USER_LIMIT:SP", max_pres)
        self.ca.set_pv_value("MN_PRESSURE:SP", min_pres)
        self.ca.set_pv_value("MX_PRESSURE:SP", max_pres)
        self.ca.set_pv_value("PRESSURE:SP", nominal_pres)
        self.ca.set_pv_value("PRESSURE_RATE:SP", pres_rate)
        self.ca.assert_that_pv_is("SEND_PARAMETERS.DISP", "0")
        self.ca.process_pv("SEND_PARAMETERS")
        self.ca.assert_that_pv_is("PRESSURE:SP:RBV", nominal_pres)
        self.ca.assert_that_pv_is("MN_PRESSURE", min_pres)
        self.ca.assert_that_pv_is("MX_PRESSURE", max_pres)
        self.ca.assert_that_pv_is("PRESSURE_RATE", pres_rate)
        # now start pumping
        self.ca.set_pv_value("RUN:SP", 1)
        self.ca.assert_that_pv_is("RUN", "Active")

    def test_WHEN_device_started_THEN_pump_and_cell_pressures_change_correctly(self):
        self.lewis.backdoor_run_function_on_device("set_pressures", [1, 3])
        self.ca.assert_that_pv_is("PRESSURE_PUMP", 1)
        self.ca.assert_that_pv_is("PRESSURE_CELL", 3)
        # default algorithm is to average pump and cell pressures
        self.ca.assert_that_pv_is("PRESSURE", 2)
        self.start_device_with_parameters(1, 50, 25, 10)
        self.ca.assert_that_pv_is("PRESSURE", 25)
        self.ca.assert_that_pv_is("PRESSURE_CELL", 25)
        self.ca.assert_that_pv_is("PRESSURE_PUMP", 25)

    @parameterized.expand(parameterized_list(itertools.product([99, 88], [44, 55])))
    def test_WHEN_difference_set_on_hardware_THEN_can_be_read_back_by_ioc(self, _, cell_pressure, pump_pressure):
        self.lewis.backdoor_run_function_on_device("set_pressures", [pump_pressure, cell_pressure])
        self.ca.assert_that_pv_is("PRESSURE_DIFF", cell_pressure - pump_pressure)

    @parameterized.expand(parameterized_list([1, 999]))
    def test_WHEN_difference_threshold_set_on_hardware_THEN_can_be_read_back_by_ioc(self, _, val):
        self.ca.set_pv_value("PRESSURE_DIFF_THOLD:SP", val)
        self.ca.assert_that_pv_is("PRESSURE_DIFF_THOLD", val)

    def test_WHEN_difference_is_greater_than_threshold_THEN_difference_is_in_alarm(self):
        pump_pressure = 100
        cell_pressure = 200

        self.lewis.backdoor_run_function_on_device("set_pressures", [pump_pressure, cell_pressure])

        diff = cell_pressure - pump_pressure

        self.ca.assert_setting_setpoint_sets_readback(diff - 1, "PRESSURE_DIFF_THOLD")
        self.ca.assert_that_pv_is("PRESSURE_DIFF", diff)
        self.ca.assert_that_pv_alarm_is("PRESSURE_DIFF", self.ca.Alarms.MAJOR)

        self.ca.assert_setting_setpoint_sets_readback(diff + 1, "PRESSURE_DIFF_THOLD")
        self.ca.assert_that_pv_is("PRESSURE_DIFF", diff)
        self.ca.assert_that_pv_alarm_is("PRESSURE_DIFF", self.ca.Alarms.NONE)

    def test_WHEN_auto_mode_is_set_THEN_auto_mode_can_be_read_back(self):
        self.lewis.backdoor_set_on_device("am_mode", 0)
        self.ca.assert_that_pv_is("INPUTS:AUTO", "Inactive")

        self.lewis.backdoor_set_on_device("am_mode", 1)
        self.ca.assert_that_pv_is("INPUTS:AUTO", "Active")

    @parameterized.expand(parameterized_list(INPUT_PVS))
    def test_WHEN_device_disconnected_THEN_inputs_go_into_alarm(self, _, pv):
        self.ca.assert_that_pv_alarm_is(pv, self.ca.Alarms.NONE)

        with self.lewis.backdoor_simulate_disconnected_device():
            self.ca.assert_that_pv_alarm_is(pv, self.ca.Alarms.INVALID)
        # Assert alarms clear on reconnection
        self.ca.assert_that_pv_alarm_is(pv, self.ca.Alarms.NONE)

    @parameterized.expand(parameterized_list(LIMIT_PVS))
    def test_WHEN_limits_are_set_THEN_limits_update(self, _, pv):
        self.ca.assert_setting_setpoint_sets_readback(5, pv)

    @parameterized.expand(parameterized_list(LIMIT_PVS))
    def test_WHEN_device_disconnected_THEN_limits_go_into_alarm(self, _, pv):
        self.ca.assert_that_pv_alarm_is(pv, self.ca.Alarms.NONE)

        with self.lewis.backdoor_simulate_disconnected_device():
            self.ca.assert_that_pv_alarm_is(pv, self.ca.Alarms.INVALID)
        # Assert alarms clear on reconnection
        self.ca.assert_that_pv_alarm_is(pv, self.ca.Alarms.NONE)

    def test_WHEN_pressure_is_too_high_THEN_reset_is_disabled(self):
        self.start_device_with_parameters(min_pres=1, max_pres=500, nominal_pres=99, pres_rate=10)
        self.ca.assert_that_pv_is("PRESSURE", 99)
        self.ca.assert_that_pv_is("RESET_PRESSURE_TOO_HIGH", "NO")
        self.ca.assert_that_pv_is("RESET:SP.DISP", "0")

        self.start_device_with_parameters(min_pres=1, max_pres=500, nominal_pres=101, pres_rate=10)
        self.ca.assert_that_pv_is("PRESSURE", 101)
        self.ca.assert_that_pv_is("RESET_PRESSURE_TOO_HIGH", "YES")
        self.ca.assert_that_pv_is("RESET:SP.DISP", "1")

    @parameterized.expand(parameterized_list([
        # DAE state, expect lock
        ("PROCESSING",  True),
        ("SETUP",      False),
        ("RUNNING",     True),
        ("PAUSED",      True),
        ("WAITING",     True),
        ("VETOING",     True),
        ("ENDING",      True),
        ("SAVING",      True),
        ("RESUMING",    True),
        ("PAUSING",     True),
        ("BEGINNING",   True),
        ("ABORTING",    True),
        ("UPDATING",    True),
        ("STORING",     True),
        ("CHANGING",    True,)
    ]))
    def test_WHEN_dae_and_manager_mode_in_certain_state_THEN_pvs_locked_accordingly(self, _, dae_state, expect_lock):
        self.ca.set_pv_value("DAE:RUNSTATE", dae_state, prefix=self.ca.host_prefix)

        for pv in PVS_LOCKED:
            self.ca.assert_that_pv_is(f"{pv}.DISP", "1" if expect_lock else "0")

    def test_WHEN_pv_locked_THEN_lock_persists(self):
        self.ca.set_pv_value("DAE:RUNSTATE", "RUNNING", prefix=self.ca.host_prefix, wait=True)

        for pv in PVS_LOCKED:
            self.ca.set_pv_value(f"{pv}.DISP", "0") # Trying to overwrite lock
            self.ca.assert_that_pv_is(f"{pv}.DISP", "1") # Checking it persists
