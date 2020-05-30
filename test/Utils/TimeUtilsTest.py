"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
import unittest

from src.Utils.TimeUtils import TimeUtils


class HumanReadableCountdown(unittest.TestCase):
  def test_seconds(self):
    self.assertEqual('Approximately 0 seconds left.',
                     TimeUtils.get_human_readable_countdown(0))
    self.assertEqual('Approximately 1 seconds left.',
                     TimeUtils.get_human_readable_countdown(1000))
    self.assertEqual('Approximately 59 seconds left.',
                     TimeUtils.get_human_readable_countdown(59 * 1000))

  def test_minutes(self):
    self.assertEqual('Approximately 1 minute left.',
                     TimeUtils.get_human_readable_countdown(60 * 1000))
    self.assertEqual('Approximately 1 minute left.',
                     TimeUtils.get_human_readable_countdown(61 * 1000))
    self.assertEqual('Approximately 2 minutes left.',
                     TimeUtils.get_human_readable_countdown(120 * 1000))
    self.assertEqual('Approximately 59 minutes left.',
                     TimeUtils.get_human_readable_countdown(3540 * 1000))

  def test_hours(self):
    self.assertEqual('Approximately 1 hour left.',
                     TimeUtils.get_human_readable_countdown(3600 * 1000))
    self.assertEqual('Approximately 1 hour, 1 minute left.',
                     TimeUtils.get_human_readable_countdown(3660 * 1000))
    self.assertEqual('Approximately 1 hour, 59 minutes left.',
                     TimeUtils.get_human_readable_countdown(7140 * 1000))
    self.assertEqual('Approximately 2 hours left.',
                     TimeUtils.get_human_readable_countdown(7200 * 1000))
    self.assertEqual('Approximately 2 hours, 1 minute left.',
                     TimeUtils.get_human_readable_countdown(7260 * 1000))
    self.assertEqual('Approximately 2 hours, 2 minutes left.',
                     TimeUtils.get_human_readable_countdown(7320 * 1000))
    self.assertEqual('Approximately 2 hours, 59 minutes left.',
                     TimeUtils.get_human_readable_countdown(10740 * 1000))
    self.assertEqual('Approximately 24 hours left.',
                     TimeUtils.get_human_readable_countdown(24 * 3600 * 1000))


if __name__ == '__main__':
  unittest.main()
