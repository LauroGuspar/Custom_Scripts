"""
Automated unit and integration tests for bt-autosuspend.
"""

import unittest
from unittest.mock import patch, MagicMock
from config import Config
from detector import Detector, BluetoothDevice
from daemon import AutoSuspendDaemon


class TestConfig(unittest.TestCase):
    def test_default_config(self):
        cfg = Config()
        self.assertEqual(cfg.idle_timeout_seconds, 120)
        self.assertEqual(cfg.detection_mode, "hybrid")
        self.assertEqual(cfg.device_filter_mode, "audio_only")
        self.assertTrue(cfg.auto_ignore_hid)
        self.assertTrue(cfg.notify_before_disconnect)
        self.assertEqual(cfg.notification_grace_seconds, 15)

    def test_filter_rules(self):
        cfg = Config(
            device_filter_mode="whitelist",
            whitelist_macs=["54:BD:79:21:EB:0C"],
            auto_ignore_hid=True,
        )
        audio_whitelisted = BluetoothDevice("54:BD:79:21:EB:0C", "Soundbar", True, True, False)
        audio_other = BluetoothDevice("9C:49:52:EA:F8:5E", "Buds", True, True, False)
        hid_dev = BluetoothDevice("AA:BB:CC:DD:EE:FF", "Mouse", True, False, True)

        # In whitelist mode: disconnect all audio EXCEPT whitelist
        # So audio_whitelisted should NOT be disconnected (managed=False)
        self.assertFalse(Detector.should_device_be_managed(audio_whitelisted, cfg))
        # audio_other is NOT in whitelist, so it SHOULD be disconnected (managed=True)
        self.assertTrue(Detector.should_device_be_managed(audio_other, cfg))
        # HID device should NEVER be disconnected
        self.assertFalse(Detector.should_device_be_managed(hid_dev, cfg))

    def test_blacklist_rules(self):
        cfg = Config(
            device_filter_mode="blacklist",
            blacklist_macs=["9C:49:52:EA:F8:5E"],
            auto_ignore_hid=True,
        )
        blacklisted = BluetoothDevice("9C:49:52:EA:F8:5E", "Buds", True, True, False)
        other = BluetoothDevice("54:BD:79:21:EB:0C", "Soundbar", True, True, False)

        self.assertTrue(Detector.should_device_be_managed(blacklisted, cfg))
        self.assertFalse(Detector.should_device_be_managed(other, cfg))


class TestDaemonLogic(unittest.TestCase):
    @patch("detector.Detector.is_playback_active")
    @patch("detector.Detector.get_paired_devices")
    @patch("subprocess.run")
    def test_daemon_idle_warning_and_disconnect(self, mock_run, mock_paired, mock_active):
        cfg = Config(
            idle_timeout_seconds=30,
            notification_grace_seconds=10,
            notify_before_disconnect=True,
            check_interval_seconds=1,
        )
        test_device = BluetoothDevice("54:BD:79:21:EB:0C", "Soundbar", True, True, False)
        mock_paired.return_value = [test_device]
        daemon = AutoSuspendDaemon(cfg)

        # 1. Active playback: timer stays 0
        mock_active.return_value = (True, "Playing")
        st = daemon.get_current_status()
        self.assertTrue(st.playback_active)
        self.assertEqual(len(st.connected_managed_devices), 1)

        # 2. Simulate disconnect method
        mock_run.return_value = MagicMock(returncode=0)
        success = daemon.disconnect_device(test_device)
        self.assertTrue(success)
        mock_run.assert_any_call(["bluetoothctl", "disconnect", "54:BD:79:21:EB:0C"], check=False, text=True, capture_output=True)


if __name__ == "__main__":
    unittest.main()
