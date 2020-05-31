"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
from typing import Optional

from PyQt5.QtCore import pyqtProperty, QTimer

# pylint:disable=import-error
from cura.PrinterOutput import PrinterOutputController
from cura.PrinterOutput.Models.PrintJobOutputModel import PrintJobOutputModel
# pylint:disable=relative-beyond-top-level
from ..utils.TimeUtils import TimeUtils


class MPSM2PrintJobOutputModel(PrintJobOutputModel):
  """Print Job Output Model."""

  POLL_INTERVAL_MILLIS = 100

  def __init__(self, output_controller: PrinterOutputController) -> None:
    """Constructor.

    Args:
      output_controller: printer's output controller.
    """
    super().__init__(output_controller=output_controller, key='', name='')
    self._state = 'not_started'
    self._progress = 0
    self._elapsed_print_time_millis = 0
    self._elapsed_percentage_points = None  # type: Optional[int]
    self._remaining_print_time_millis = 24 * 60 * 60 * 1000  # arbitrary max
    self._stopwatch = QTimer(self)
    self._stopwatch.timeout.connect(self._tick)

  # Override.
  # Superclass computes progress based on elapsed time, whereas MPSM2 printers
  # respond with progress in percentage points.
  @pyqtProperty(float)
  def progress(self) -> float:
    """
    Returns:
      Print job progress from 0.0 to 100.0.
    """
    return self._progress

  @pyqtProperty(str)
  def estimated_time_left(self) -> str:
    """
    Returns:
       Human-readable estimated printing time left.
    """
    if not self._elapsed_percentage_points \
        or self._elapsed_percentage_points < 2:
      return ''

    return TimeUtils.get_human_readable_countdown(
        self._remaining_print_time_millis / 1000)

  def update_progress(self, progress: float) -> None:
    """Updates job progress and calculates estimated printing time left.

    Args:
      progress: job progress from 0.0 to 100.0.
    """
    if self._progress != progress:
      self._progress = progress
      if self._progress == 0:
        self._elapsed_print_time_millis = 0
        self._stopwatch.stop()
      else:
        self._calculate_remaining_print_time()

  def _calculate_remaining_print_time(self) -> None:
    """Calculates remaining print time based on the running time of percentage
    points."""
    if self._elapsed_print_time_millis == 0 and not self._stopwatch.isActive():
      self._stopwatch.start(self.POLL_INTERVAL_MILLIS)
      return

    if self._elapsed_percentage_points is None:
      self._elapsed_percentage_points = 0
    else:
      self._elapsed_percentage_points += 1
      new_remaining_time = (100 - self._progress) \
                           * self._elapsed_print_time_millis \
                           / self._elapsed_percentage_points
      # Only go down
      if new_remaining_time < self._remaining_print_time_millis:
        self._remaining_print_time_millis = new_remaining_time

  def _tick(self):
    """Updates stopwatch."""
    self._elapsed_print_time_millis += self.POLL_INTERVAL_MILLIS
