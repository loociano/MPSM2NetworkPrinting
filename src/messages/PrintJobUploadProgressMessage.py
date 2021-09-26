"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
from typing import Callable

from PyQt5.QtCore import QTimer

from UM import i18nCatalog
from UM.Message import Message
from ..utils import TimeUtils

I18N_CATALOG = i18nCatalog('cura')


class PrintJobUploadProgressMessage(Message):
  """Message displayed when a print upload is in progress."""

  MIN_CALCULATION_TIME_MILLIS = 5000
  POLL_TIME_MILLIS = 10
  MAX_REMAINING_MILLIS = 24 * 60 * 60 * 1000  # arbitrary max
  CALCULATING_TEXT = I18N_CATALOG.i18nc('@info:status',
                                        'Calculating time left...')

  def __init__(self, on_cancelled: Callable) -> None:
    """Constructor.

    Args:
      on_cancelled: Called when user cancels printer upload.
    """
    super().__init__(
        title=I18N_CATALOG.i18nc('@info:status', 'Uploading model to printer'),
        text=self.CALCULATING_TEXT,
        progress=-1,
        lifetime=0,
        dismissable=False,
        use_inactivity_timer=False)
    self._on_cancelled = on_cancelled
    self._elapsed_upload_time_millis = 0
    self._remaining_time_millis = self.MAX_REMAINING_MILLIS
    self.addAction('cancel', I18N_CATALOG.i18nc('@action:button', 'Cancel'),
                   'cancel',
                   I18N_CATALOG.i18nc('@action', 'Cancels job upload.'))
    self.actionTriggered.connect(self._on_action_triggered)
    self._stopwatch = QTimer(self)
    self._stopwatch.timeout.connect(self._tick)
    self._reset_calculation_time()

  def show(self) -> None:
    """See base class."""
    self.setProgress(0)
    super().show()
    self._stopwatch.start(self.POLL_TIME_MILLIS)
    self._reset_calculation_time()

  def hide(self, send_signal=True) -> None:
    """See base class."""
    super().hide()
    self._stopwatch.stop()
    self._reset_calculation_time()

  def update(self, bytes_sent: int, bytes_total: int) -> None:
    """Updates the progress bar.

    Args:
      bytes_sent: Number of bytes sent.
      bytes_total: Target bytes.
    """
    percentage = (bytes_sent / bytes_total) if bytes_total else 0
    self.setProgress(percentage * 100)
    if self._elapsed_upload_time_millis > self.MIN_CALCULATION_TIME_MILLIS:
      speed = bytes_sent / self._elapsed_upload_time_millis
      remaining_millis = (bytes_total - bytes_sent) / speed if speed else 0
      # Only go down.
      if remaining_millis < self._remaining_time_millis:
        self._remaining_time_millis = remaining_millis
        self.setText(
            TimeUtils.get_human_readable_countdown(
                seconds=int(remaining_millis / 1000)))

  def _reset_calculation_time(self) -> None:
    """Resets the estimated calculation time."""
    self._elapsed_upload_time_millis = 0
    self._remaining_time_millis = self.MAX_REMAINING_MILLIS
    self.setText(self.CALCULATING_TEXT)

  def _on_action_triggered(self, message: str, action: str) -> None:
    """Called when an action from user was triggered.

    Args:
      message: Message (ignored).
      action: Action triggered.
    """
    if action == 'cancel':
      self._on_cancelled()

  def _tick(self) -> None:
    """Updates stopwatch."""
    self._elapsed_upload_time_millis += self.POLL_TIME_MILLIS
