"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""


class TimeUtils:
  @staticmethod
  def get_human_readable_countdown(millis: float) -> str:
    """
    Args:
      millis: time in milliseconds.

    Returns:
      Human-readable count down.
    """
    minutes = millis / 60000
    seconds = (millis / 1000) % 60
    if minutes >= 1:
      if round(minutes) == 1:
        return 'Approximately 1 minute left.'
      return 'Approximately {} minutes left. '.format(round(minutes))
    return 'Approximately {} seconds left.'.format(round(seconds))
