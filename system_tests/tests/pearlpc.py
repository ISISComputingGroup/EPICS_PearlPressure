import unittest
from time import sleep

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.testing import get_running_lewis_and_ioc, assert_log_messages, skip_if_recsim, unstable_test
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

    @parameterized.expand([
        (True, "set_em_stop_status", 0, 1, 1),
        (True, "set_ru", 1, 1, 1),
        (True, "set_re", 2, 1, 1),
        (True, "set_stop_bit", 3, 1, 1),
        (True, "set_by", 4, 1, 1),
        (True, "set_go", 5, 1, 1),
        (True, "set_am", 6, 1, 1),
        (False, "SL_PRESSURE", 7, "Closed Loop", 1),
        (True, "set_er", 9, 1, 1),
        (False, "PRESSURE_RATE", 10, 35, 35),
        (False, "MN_PRESSURE", 11, 35, 35),
        (False, "SP_PRESSURE", 12, 35, 35),
        (False, "MX_PRESSURE", 13, 35, 35)
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

    def test_WHEN_initial_ID_prefix_set_THEN_initial_ID_prefix_read_back_correctly(self):
        self.ca.set_pv_value("SI_PRESSURE:SP", self.pressure_value)
        self.ca.assert_that_pv_is("SI_PRESSURE:SP", self.pressure_value)

    def test_WHEN_secondary_ID_prefix_set_THEN_secondary_ID_prefix_read_back_correctly(self):
        self.ca.set_pv_value("SD_PRESSURE:SP", self.pressure_value)
        self.ca.assert_that_pv_is("SD_PRESSURE:SP", self.pressure_value)

    def test_WHEN_id_prefixes_not_set_THEN_default_id_prefixes_read_back_correctly(self):
        self.ca.assert_that_pv_is("ID_PRESSURE", f"{self.default_id_prefix} {self.default_id_prefix}")

    def test_WHEN_id_prefixes_set_THEN_id_prefixes_read_back_correctly(self):
        self.ca.set_pv_value("SI_PRESSURE:SP", self.pressure_value)
        self.ca.set_pv_value("SD_PRESSURE:SP", self.pressure_value)
        self.ca.assert_that_pv_is("ID_PRESSURE", f"{self.pressure_value:04d} {self.pressure_value:04d}")

    def test_WHEN_pressure_set_lower_than_drvl_field_THEN_read_back_correctly(self):
        self.ca.set_pv_value("MN_PRESSURE:SP", 10)
        self.ca.set_pv_value("SP_PRESSURE:SP", 5)
        self.ca.process_pv("SEND_PARAMETERS")
        self.ca.assert_that_pv_is("SP_PRESSURE:SP", 10)

    def test_WHEN_reset_bit_value_set_THEN_reset_bit_value_read_back_correctly_HIGH_PRESSURE(self):
        self.ca.set_pv_value("RESET_PRESSURE:SP", 0)
        self.ca.set_pv_value("MN_PRESSURE:SP", 10)
        self.ca.process_pv("SEND_PARAMETERS")
        self.ca.assert_setting_setpoint_sets_readback(35, "SP_PRESSURE")
        self.ca.set_pv_value("RESET_PRESSURE:SP", 1)
        self.ca.assert_that_pv_is("RESET_PRESSURE_STATUS", 1)

    def test_WHEN_General_error_occurs_THEN_general_error_readback_correctly(self):
        self.ca.assert_that_pv_is("GENERAL_ERROR", "OFF")
        self.lewis.backdoor_run_function_on_device("set_er", [1])
        self.ca.assert_that_pv_is("GENERAL_ERROR", "ON")

    def test_WHEN_value_set_THEN_status_readback_correctly(self):
        self.ca.set_pv_value("PRESSURE_RATE:SP", 35)
        self.ca.process_pv("SEND_PARAMETERS")
        self.ca.assert_that_pv_is("PRESSURE_RATE", 35)

    def test_WHEN_correct_conditions_met_THEN_device_ready_state_readback_correctly(self):
        self.ca.assert_that_pv_is("READY_STATE", "READY")

    def test_WHEN_conditions_are_not_met_THEN_device_ready_state_readback_correctly(self):
        self.ca.set_pv_value("RESET_PRESSURE:SP", 1)
        self.ca.assert_that_pv_is("READY_STATE", "NOT READY")

    def start_device_with_parameters(self, min_pres, max_pres, nominal_pres, pres_rate):
        self.ca.set_pv_value("MN_PRESSURE:SP", min_pres)
        self.ca.set_pv_value("MX_PRESSURE:SP", max_pres)
        self.ca.set_pv_value("SP_PRESSURE:SP", nominal_pres)
        self.ca.set_pv_value("PRESSURE_RATE:SP", pres_rate)
        self.ca.set_pv_value("RUN", 1)
        self.ca.process_pv("SEND_PARAMETERS")

    @parameterized.expand([
        (50, 25),
        (50, 75),
    ])
    def test_WHEN_device_started_THEN_pressure_increasing_decreasing_set_correctly(self, target_pressure, test_pressure):
        self.start_device_with_parameters(0, target_pressure + 50, target_pressure, 50)
        self.ca.assert_that_pv_is("INCREASING_PRESSURE", "Increasing")
        self.ca.assert_that_pv_is("DECREASING_PRESSURE", "Nominal")
        # Wait for desired pressure to be achieved. Rate is high so it shouldn't exceed timeout
        self.ca.assert_that_pv_is("INCREASING_PRESSURE", "Nominal")
        self.ca.assert_that_pv_is("DECREASING_PRESSURE", "Nominal")
        self.start_device_with_parameters(0, test_pressure + 50, test_pressure, 50)
        test_increase = "Increasing" if test_pressure > target_pressure else "Nominal"
        test_decrease = "Decreasing" if test_pressure < target_pressure else "Nominal"
        self.ca.assert_that_pv_is("INCREASING_PRESSURE", test_increase)
        self.ca.assert_that_pv_is("DECREASING_PRESSURE", test_decrease)
        # Wait for desired pressure to be achieved. Rate is high so it shouldn't exceed timeout
        self.ca.assert_that_pv_is("INCREASING_PRESSURE", "Nominal")
        self.ca.assert_that_pv_is("DECREASING_PRESSURE", "Nominal")

    def test_WHEN_device_started_THEN_pump_and_cell_pressures_change_correctly(self):
        self.lewis.backdoor_run_function_on_device("set_pressures", [0, 0])
        self.ca.assert_that_pv_is("PRESSURE_CELL", 0)
        self.ca.assert_that_pv_is("PRESSURE_PUMP", 0)
        self.start_device_with_parameters(0, 50, 25, 10)
        self.ca.assert_that_pv_is_not("PRESSURE_CELL", 0)
        self.ca.assert_that_pv_is_not("PRESSURE_PUMP", 0)
