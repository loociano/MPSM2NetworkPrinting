"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
import unittest

from src.utils import TimeUtils


class HumanReadableCountdown(unittest.TestCase):
  def test_convertSeconds_succeeds(self):
    self.assertEqual('Approximately 0 seconds left.',
                     TimeUtils.get_human_readable_countdown(0))
    self.assertEqual('Approximately 1 seconds left.',
                     TimeUtils.get_human_readable_countdown(1))
    self.assertEqual('Approximately 59 seconds left.',
                     TimeUtils.get_human_readable_countdown(59))

  def test_convertMinutes_succeeds(self):
    self.assertEqual('Approximately 1 minute left.',
                     TimeUtils.get_human_readable_countdown(60))
    self.assertEqual('Approximately 1 minute left.',
                     TimeUtils.get_human_readable_countdown(61))
    self.assertEqual('Approximately 2 minutes left.',
                     TimeUtils.get_human_readable_countdown(120))
    self.assertEqual('Approximately 59 minutes left.',
                     TimeUtils.get_human_readable_countdown(3600 - 60))

  def test_convertHours_succeeds(self):
    self.assertEqual('Approximately 1 hour left.',
                     TimeUtils.get_human_readable_countdown(3600))
    self.assertEqual('Approximately 1 hour, 1 minute left.',
                     TimeUtils.get_human_readable_countdown(3600 + 60))
    self.assertEqual('Approximately 1 hour, 59 minutes left.',
                     TimeUtils.get_human_readable_countdown(7200 - 60))
    self.assertEqual('Approximately 2 hours left.',
                     TimeUtils.get_human_readable_countdown(7200))
    self.assertEqual('Approximately 2 hours, 1 minute left.',
                     TimeUtils.get_human_readable_countdown(7200 + 60))
    self.assertEqual('Approximately 2 hours, 2 minutes left.',
                     TimeUtils.get_human_readable_countdown(7200 + 120))
    self.assertEqual('Approximately 2 hours, 59 minutes left.',
                     TimeUtils.get_human_readable_countdown(3 * 3600 - 60))
    self.assertEqual('Approximately 24 hours left.',
                     TimeUtils.get_human_readable_countdown(24 * 3600))


if __name__ == '__main__':
  unittest.main()
