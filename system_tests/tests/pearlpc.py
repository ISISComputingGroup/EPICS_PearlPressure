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
        self.lewis, self.ioc = get_running_lewis_and_ioc(DEVICE_A_PREFIX, DEVICE_A_PREFIX)
        self.ca = ChannelAccess(default_timeout=20, default_wait_time=0.0, device_prefix=DEVICE_A_PREFIX)

    def test_WHEN_max_pressure_set_THEN_max_pressure_set_correctly(self):
        self.ca.set_pv_value("MX_PRESSURE:SP", self.pressure_value)
        self.ca.assert_that_pv_is("MX_PRESSURE:SP", self.pressure_value)
        self.ca.assert_that_pv_is("BUFFER2.C", self.pressure_value)
        # self.ca.assert_setting_setpoint_sets_readback(self.pressure_value, "MX_PRESSURE")

    def test_WHEN_pressure_set_THEN_pressure_read_back_correctly(self):
        self.ca.set_pv_value("PRESSURE:SP", self.pressure_value)
        self.ca.assert_that_pv_is("PRESSURE:SP", self.pressure_value)
        self.ca.assert_that_pv_is("BUFFER1.K", self.pressure_value)
        # self.ca.assert_setting_setpoint_sets_readback(self.pressure_value, "PRESSURE")

    def test_WHEN_min_pressure_set_THEN_min_pressure_read_back_correctly(self):
        self.ca.set_pv_value("MN_PRESSURE:SP", self.pressure_value)
        self.ca.assert_that_pv_is("MN_PRESSURE:SP", self.pressure_value)
        self.ca.assert_that_pv_is("BUFFER2.A", self.pressure_value)
        # self.ca.assert_setting_setpoint_sets_readback(self.pressure_value, "MN_PRESSURE")

    def test_WHEN_setpoint_pressure_set_THEN_setpoint_pressure_read_back_correctly(self):
        self.ca.set_pv_value("SP_PRESSURE:SP", self.pressure_value)
        self.ca.assert_that_pv_is("SP_PRESSURE:SP", self.pressure_value)
        self.ca.assert_that_pv_is("BUFFER2.B", self.pressure_value)
        # self.ca.assert_setting_setpoint_sets_readback(self.pressure_value, "SP_PRESSURE")

    def test_WHEN_Seal_Fail_pressure_set_THEN_Seal_Fail_pressure_read_back_correctly(self):
        self.ca.set_pv_value("SF_PRESSURE:SP", self.pressure_value)
        self.ca.assert_that_pv_is("SF_PRESSURE:SP", self.pressure_value)
        self.ca.assert_that_pv_is("BUFFER1.I", self.pressure_value)
        # self.ca.assert_setting_setpoint_sets_readback(self.pressure_value, "SF_PRESSURE")

    def test_WHEN_initial_ID_prefix_set_THEN_initial_ID_prefix_read_back_correctly(self):
        self.ca.set_pv_value("SI_PRESSURE:SP", self.pressure_value)
        self.ca.assert_that_pv_is("SI_PRESSURE:SP", self.pressure_value)
        # self.ca.assert_setting_setpoint_sets_readback(self.pressure_value, "SI_PRESSURE")

    def test_WHEN_secondary_ID_prefix_set_THEN_secondary_ID_prefix_read_back_correctly(self):
        self.ca.set_pv_value("SD_PRESSURE:SP", self.pressure_value)
        self.ca.assert_that_pv_is("SD_PRESSURE:SP", self.pressure_value)
        # self.ca.assert_setting_setpoint_sets_readback(self.pressure_value, "SD_PRESSURE")

    def test_WHEN_id_prefixes_set_THEN_id_prefixes_read_back_correctly(self):
        self.ca.set_pv_value("SI_PRESSURE:SP", self.pressure_value)
        self.ca.set_pv_value("SD_PRESSURE:SP", self.pressure_value)
        self.ca.assert_that_pv_is("ID_PRESSURE", f"{self.pressure_value} {self.pressure_value}")

    def test_WHEN_loop_mode_set_THEN_loop_mode_read_back_correctly(self):
        self.ca.set_pv_value("SL_PRESSURE:SP", self.set_loop_status)
        self.ca.assert_that_pv_is("SL_PRESSURE:SP", self.set_loop_status)
        self.ca.assert_that_pv_is("BUFFER1.H", self.set_loop_status)

    def test_WHEN_busy_bit_set_THEN_busy_bit_read_back_correctly(self):
        self.ca.set_pv_value("BY_PRESSURE:SP", self.set_loop_status)
        self.ca.assert_that_pv_is("BY_PRESSURE:SP", self.set_loop_status)
        self.ca.assert_that_pv_is("BUFFER1.E", self.set_loop_status)
        # self.ca.assert_that_pv_is("BUFFER1.E", str(self.set_loop_status)) #TODO Fix buffer read test

    def test_WHEN_run_bit_set_THEN_run_bit_read_back_correctly(self):
        self.ca.set_pv_value("RU_PRESSURE:SP", self.set_loop_status)
        self.ca.assert_that_pv_is("RU_PRESSURE:SP", self.set_loop_status)
        self.ca.assert_that_pv_is("BUFFER1.B", self.set_loop_status)

    def test_WHEN_reset_value_set_THEN_reset_value_read_back_correctly(self):
        self.ca.set_pv_value("RE_PRESSURE:SP", self.set_loop_status)
        self.ca.assert_that_pv_is("RE_PRESSURE:SP", self.set_loop_status)
        self.ca.assert_that_pv_is("BUFFER1.C", self.set_loop_status)

    def test_WHEN_stop_bit_set_THEN_stop_bit_value_read_back_correctly(self):
        self.ca.set_pv_value("St_PRESSURE:SP", self.set_loop_status)
        self.ca.assert_that_pv_is("St_PRESSURE:SP", self.set_loop_status)
        self.ca.assert_that_pv_is("BUFFER1.D", self.set_loop_status)

    def test_WHEN_em_stop_bit_set_THEN_em_stop_bit_value_read_back_correctly(self):
        self.ca.set_pv_value("EM_PRESSURE:SP", self.set_loop_status)
        self.ca.assert_that_pv_is("EM_PRESSURE:SP", self.set_loop_status)
        self.ca.assert_that_pv_is("BUFFER1.A", self.set_loop_status)

    def test_WHEN_er_last_error_code_set_THEN_er_last_error_code_read_back_correctly(self):
        self.ca.set_pv_value("ER_PRESSURE:SP", self.set_loop_status)
        self.ca.assert_that_pv_is("ER_PRESSURE:SP", self.set_loop_status)
        self.ca.assert_that_pv_is("BUFFER1.J", self.set_loop_status)

    def test_WHEN_AM_mode_set_THEN_AM_mode_read_back_correctly(self):
        self.ca.set_pv_value("AM_PRESSURE:SP", self.set_loop_status)
        self.ca.assert_that_pv_is("AM_PRESSURE:SP", self.set_loop_status)
        self.ca.assert_that_pv_is("BUFFER1.G", self.set_loop_status)

    def test_WHEN_GO_status_set_THEN_GO_status_read_back_correctly(self):
        self.ca.set_pv_value("GO_PRESSURE:SP", self.set_loop_status)
        self.ca.assert_that_pv_is("GO_PRESSURE:SP", self.set_loop_status)
        self.ca.assert_that_pv_is("BUFFER1.F", self.set_loop_status)
