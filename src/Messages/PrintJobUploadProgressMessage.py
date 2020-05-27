"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
from typing import Callable

from PyQt5.QtCore import QTimer

from UM import i18nCatalog
from UM.Message import Message

I18N_CATALOG = i18nCatalog('cura')


class PrintJobUploadProgressMessage(Message):
  """Message displayed when a print upload is in progress."""

  MIN_CALCULATION_TIME_MILLIS = 5000
  CALCULATING_TEXT = I18N_CATALOG.i18nc('@info:status',
                                        'Calculating time left...')

  def __init__(self, on_cancelled: Callable) -> None:
    super().__init__(
        title=I18N_CATALOG.i18nc('@info:status', 'Uploading model to printer'),
        text=self.CALCULATING_TEXT,
        progress=-1,
        lifetime=0,
        dismissable=False,
        use_inactivity_timer=False)
    self._on_cancelled = on_cancelled
    self.addAction('cancel', I18N_CATALOG.i18nc('@action:button', 'Cancel'),
                   'cancel',
                   I18N_CATALOG.i18nc('@action', 'Cancels job upload.'))
    self.actionTriggered.connect(self._on_action_triggered)
    self._stopwatch = QTimer(self)
    self._stopwatch.timeout.connect(self._tick)
    self._reset_calculation_time()

  # Override
  def show(self) -> None:
    """Shows the message."""
    self.setProgress(0)
    super().show()
    self._stopwatch.start(10)  # milliseconds
    self._reset_calculation_time()

  # Override
  def hide(self, send_signal=True) -> None:
    """Hides the message"""
    super().hide()
    self._stopwatch.stop()
    self._reset_calculation_time()

  def update(self, bytes_sent: int, bytes_total: int) -> None:
    """Updates the progress bar.

    Args:
      bytes_sent: number of bytes sent
      bytes_total: target bytes
    """
    percentage = (bytes_sent / bytes_total) if bytes_total else 0
    if self._upload_time_millis > self.MIN_CALCULATION_TIME_MILLIS:
      speed = bytes_sent / self._upload_time_millis
      remaining_millis = (bytes_total - bytes_sent) / speed if speed else 0
      self.setText(self._get_human_readable_countdown(remaining_millis))
    self.setProgress(percentage * 100)

  def _reset_calculation_time(self):
    """Resets the estimated calculation time."""
    self._upload_time_millis = 0
    self.setText(self.CALCULATING_TEXT)

  @staticmethod
  def _get_human_readable_countdown(millis: float) -> str:
    """
    Args:
      millis: time in milliseconds.

    Returns:
      Human-readable count down.
    """
    minutes = round(millis / 60000)
    seconds = round((millis / 1000) % 60)
    if minutes > 0:
      if minutes == 1:
        return 'Approximately 1 minute left.'
      return 'Approximately {} minutes left. '.format(minutes)
    return 'Approximately {} seconds left.'.format(seconds)

  def _on_action_triggered(self, message: str, action: str) -> None:
    """Called when an action from user was triggered.

    Args:
      message: message (ignored)
      action: action triggered
    """
    if action == 'cancel':
      self._on_cancelled()

  def _tick(self):
    """Updates stopwatch."""
    self._upload_time_millis += 10
