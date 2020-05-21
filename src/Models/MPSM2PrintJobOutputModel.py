"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
from PyQt5.QtCore import pyqtProperty, pyqtSignal

from cura.PrinterOutput import PrinterOutputController
from cura.PrinterOutput.Models.PrintJobOutputModel import PrintJobOutputModel


class MPSM2PrintJobOutputModel(PrintJobOutputModel):
  """Print Job Output Model."""
  _timeElapsedChanged = pyqtSignal()

  def __init__(self, output_controller: PrinterOutputController) -> None:
    """Constructor.

    Args:
      output_controller: printer's output controller.
    """
    super().__init__(output_controller=output_controller, key='', name='')
    self._state = 'not_started'
    self._progress = 0
    self.timeElapsedChanged.connect(self._timeElapsedChanged)

  # Override
  @pyqtProperty(float, notify=_timeElapsedChanged)
  def progress(self) -> float:
    """Indicates print job progress.

    Returns:
      Print job progress from 0 to 1.
    """
    return self._progress

  def update_progress(self, progress: float) -> None:
    """Updates job progress.

    Args:
      progress: job progress from 0 to 1.
    """
    self._progress = progress

  def get_state(self) -> str:
    """Gets job state.

    Returns:
      Job state.
    """
    return self._state
