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
        self.pressure_value = 1000
        self.set_loop_status = 1
        self.default_initial_value = 0
        self.default_id_prefix = 1111
        self.low_pressure = 50
        self.lewis, self.ioc = get_running_lewis_and_ioc(DEVICE_A_PREFIX, DEVICE_A_PREFIX)
        self.ca = ChannelAccess(default_timeout=20, default_wait_time=0.0, device_prefix=DEVICE_A_PREFIX)
        self.lewis.backdoor_run_function_on_device("re_initialise")

    @parameterized.expand([
        ("EM_PRESSURE", "EM_PRESSURE",  0, "Stop", 1),
        ("RU_PRESSURE", "RU_PRESSURE",  1, "Stop", 1),
        ("RE_PRESSURE", "RE_PRESSURE",  2, "Reset complete", 1),
        ("ST_PRESSURE", "ST_PRESSURE",  3, "Stopped", 1),
        ("BY_PRESSURE", "BY_PRESSURE",  4, "Active", 1),
        ("GO_PRESSURE", "GO_PRESSURE",  5, "TRUE", 1),
        ("AM_PRESSURE", "AM_PRESSURE",  6, "Auto", 1),
        ("SL_PRESSURE", "SL_PRESSURE",  7, "Closed Loop", 1),
        ("SF_PRESSURE", "SF_PRESSURE",  8, 1, 1),
        ("ER_PRESSURE", "ER_PRESSURE",  9, 1, 1),
        ("PRESSURE",    "PRESSURE",    10, 1000, 1000),
        ("MN_PRESSURE", "MN_PRESSURE", 11, 1000, 1000),
        ("SP_PRESSURE", "SP_PRESSURE", 12, 1000, 1000),
        ("MX_PRESSURE", "MX_PRESSURE", 13, 1000, 1000)
    ])
    def test_WHEN_pv_set_THEN_pv_and_buffer_readback_correctly(self, _, pv_record, buffer_location, setpoint_value, buffer_value):
        self.ca.set_pv_value("{}:SP".format(pv_record), setpoint_value)
        self.ca.assert_that_pv_is(pv_record, setpoint_value)
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
        self.ca.assert_that_pv_is("ID_PRESSURE", f"{self.pressure_value} {self.pressure_value}")

    def test_WHEN_pressure_set_lower_than_drvl_field_THEN_read_back_correctly(self):
        self.ca.set_pv_value("MN_PRESSURE:SP", 10)
        self.ca.set_pv_value("PRESSURE:SP", 5)
        self.ca.assert_that_pv_is("PRESSURE", 10)

    def test_WHEN_reset_bit_value_set_THEN_reset_bit_value_read_back_correctly_HIGH_PRESSURE(self):
        self.ca.set_pv_value("RESET_PRESSURE:SP", 0)
        self.ca.set_pv_value("MN_PRESSURE:SP", 10)
        self.ca.assert_setting_setpoint_sets_readback(500, "PRESSURE")
        self.ca.set_pv_value("RESET_PRESSURE:SP", 1)
        self.ca.assert_that_pv_is("RESET_PRESSURE", "RESET")

    def test_WHEN_General_error_occurs_THEN_general_error_readback_correctly(self):
        self.ca.assert_that_pv_is("GENERAL_ERROR", "OFF")
        self.ca.set_pv_value("ER_PRESSURE:SP", 1)
        self.ca.assert_that_pv_is("GENERAL_ERROR", "ON")

    def test_WHEN_value_set_THEN_status_readback_correctly(self):
        self.ca.set_pv_value("PRESSURE:SP", 500)
        self.ca.assert_that_pv_is("STATUS_ARRAY", [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 500, 0, 0, 0, 0])

    def test_WHEN_np_pv_set_THEN_intitial_buffer_value_readback_correctly(self):
        self.ca.assert_that_pv_is("STATUS_ARRAY", [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

    def test_WHEN_correct_conditions_met_THEN_device_ready_state_readback_correctly(self):
        self.ca.assert_that_pv_is("READY_STATE", "READY")

    def test_WHEN_conditions_are_not_met_THEN_device_ready_state_readback_correctly(self):
        self.ca.set_pv_value("RESET_PRESSURE", 1)
        self.ca.assert_that_pv_is("READY_STATE", "NOT READY")



