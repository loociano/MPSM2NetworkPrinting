"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
from datetime import timedelta
from typing import Optional

from PyQt5.QtCore import pyqtProperty, QTimer

# pylint:disable=import-error
from cura.PrinterOutput import PrinterOutputController
from cura.PrinterOutput.Models.PrintJobOutputModel import PrintJobOutputModel
# pylint:disable=relative-beyond-top-level
from ..utils.TimeUtils import TimeUtils

_POLL_INTERVAL_MILLIS = 100
_MIN_PERCENT_POINTS = 2  # Minimum points to calculate estimated time left.
# Arbitrary maximum.
_MAX_REMAINING_TIME_SECS = timedelta(days=1).total_seconds()


class MPSM2PrintJobOutputModel(PrintJobOutputModel):
  """Print Job Output Model."""

  def __init__(self, output_controller: PrinterOutputController) -> None:
    """Constructor.

    Args:
      output_controller: Printer's output controller.
    """
    super().__init__(output_controller=output_controller, key='', name='')
    self._state = 'not_started'
    self._progress = 0  # type: int
    self._elapsed_print_time_millis = 0  # type: int
    self._elapsed_percentage_points = None  # type: Optional[int]
    # Estimated printing time left, in seconds.
    self._remaining_print_time_secs = _MAX_REMAINING_TIME_SECS
    self._stopwatch = QTimer(self)
    self._stopwatch.timeout.connect(self._tick)
    self._reset()

  # Override.
  # Superclass computes progress based on elapsed time.
  # MPSM2 printers do not provide elapsed time, but progress in percentage.
  @pyqtProperty(int)
  def progress(self) -> int:
    """UI label for printing progress.

    Returns:
      Print job progress from 0 to 100.
    """
    return self._progress

  @pyqtProperty(str)
  def estimated_time_left(self) -> str:
    """UI label for estimated time left.

    Returns:
       Human-readable estimated printing time left.
    """
    if self._elapsed_percentage_points is None:
      return ''
    if self._elapsed_percentage_points < _MIN_PERCENT_POINTS:
      return ''
    return TimeUtils.get_human_readable_countdown(
        seconds=self._remaining_print_time_secs)

  def update_progress(self, progress: int) -> None:
    """Updates job progress and calculates estimated printing time left.

    Args:
      progress: Job progress from 0 to 100.
    """
    if progress < 0 or progress > 100:
      raise ValueError(f'Invalid printing progress: {progress}.')
    if progress == 0:
      self._reset()
    elif self._progress != progress:
      if self._elapsed_percentage_points is None:
        # Skip first seen percent point.
        self._elapsed_percentage_points = 0
      elif self._elapsed_percentage_points == 0:
        self._elapsed_percentage_points += 1
        if not self._stopwatch.isActive():
          # New percent point seen. Start measuring.
          self._stopwatch.start(_POLL_INTERVAL_MILLIS)
      else:
        self._remaining_print_time_secs = self._calculate_remaining_print_time()
        self._elapsed_percentage_points += 1
    self._progress = progress

  def _reset(self) -> None:
    """Resets variables to calculate estimated print time left."""
    self._elapsed_print_time_millis = 0
    self._elapsed_percentage_points = None
    self._remaining_print_time_secs = _MAX_REMAINING_TIME_SECS
    if self._stopwatch.isActive():
      self._stopwatch.stop()

  def _calculate_remaining_print_time(self) -> int:
    """Calculates remaining print time.

    Calculation is based on the printing time and progress so far.

    Returns
      Remaining print time in seconds.
    """
    return int((100 - self._progress)
        * self._elapsed_print_time_millis
        / self._elapsed_percentage_points / 1000)


  def _tick(self) -> None:
    """Updates stopwatch."""
    self._elapsed_print_time_millis += _POLL_INTERVAL_MILLIS
