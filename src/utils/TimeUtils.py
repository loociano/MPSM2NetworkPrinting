"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
from math import floor


class TimeUtils:
  """Utilities to display time."""

  @staticmethod
  def get_human_readable_countdown(seconds: float) -> str:
    """
    Args:
      seconds: countdown in number of seconds.

    Returns:
      Human-readable count down.
    """
    hours = seconds / 3600
    if hours >= 1:
      hours = floor(hours)
      minutes = round((seconds / 60) % 60)
      return 'Approximately {}{} left.' \
        .format('{} {}'
                .format(hours, 'hours' if hours > 1 else 'hour'),
                ', {} {}'.format(minutes,
                                 'minutes' if minutes > 1 else 'minute')
                if minutes > 0 else '')

    minutes = seconds / 60
    if minutes >= 1:
      if round(minutes) == 1:
        return 'Approximately 1 minute left.'
      return 'Approximately {} minutes left.'.format(round(minutes))
    return 'Approximately {} seconds left.'.format(round(seconds % 60))
