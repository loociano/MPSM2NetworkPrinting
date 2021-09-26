"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
from math import floor


class TimeUtils:
  """Utilities to display time."""

  @staticmethod
  def get_human_readable_countdown(seconds: int) -> str:
    """
    Args:
      seconds: Countdown in number of seconds.

    Returns:
      Human-readable count down.
    """
    if seconds / 3600 >= 1:
      return TimeUtils._get_countdown_with_hours(seconds)
    if seconds / 60 >= 1:
      return TimeUtils._get_countdown_with_minutes(round(seconds / 60))
    return f'Approximately {seconds} seconds left.'

  @staticmethod
  def _get_countdown_with_hours(seconds: int) -> str:
    hours = floor(seconds / 3600)
    minutes = round((seconds / 60) % 60)
    hours_str = f'{hours} hours' if hours > 1 else '1 hour'
    minutes_str = f'{minutes} minutes' if minutes > 1 else '1 minute'
    countdown_str = f'{hours_str}, {minutes_str}' if minutes > 0 else hours_str
    return f'Approximately {countdown_str} left.'

  @staticmethod
  def _get_countdown_with_minutes(minutes: int) -> str:
    if minutes == 1:
      return 'Approximately 1 minute left.'
    return f'Approximately {minutes} minutes left.'
