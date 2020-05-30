"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
from math import floor


class TimeUtils:
  """Utilities to display time."""

  @staticmethod
  def get_human_readable_countdown(millis: float) -> str:
    """
    Args:
      millis: time in milliseconds.

    Returns:
      Human-readable count down.
    """
    hours = millis / 3600000
    if hours >= 1:
      hours = floor(hours)
      minutes = round((millis / 60000) % 60)
      return 'Approximately {}{} left.' \
        .format('{} {}'
                .format(hours, 'hours' if hours > 1 else 'hour'),
                ', {} {}'.format(minutes,
                                 'minutes' if minutes > 1 else 'minute')
                if minutes > 0 else '')

    minutes = millis / 60000
    seconds = (millis / 1000) % 60
    if minutes >= 1:
      if round(minutes) == 1:
        return 'Approximately 1 minute left.'
      return 'Approximately {} minutes left.'.format(round(minutes))
    return 'Approximately {} seconds left.'.format(round(seconds))
