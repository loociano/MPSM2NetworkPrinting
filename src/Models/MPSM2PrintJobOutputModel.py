# Copyright 2020 Luc Rubio <luc@loociano.com>
# Plugin is licensed under the GNU Lesser General Public License v3.0.
from PyQt5.QtCore import pyqtProperty, pyqtSignal

from cura.PrinterOutput import PrinterOutputController
from cura.PrinterOutput.Models.PrintJobOutputModel import PrintJobOutputModel


class MPSM2PrintJobOutputModel(PrintJobOutputModel):
    _timeElapsedChanged = pyqtSignal()
    def __init__(self, output_controller: PrinterOutputController) -> None:
        super().__init__(output_controller=output_controller, key='', name='')
        self._state = 'not_started'
        self._progress = 0
        self.timeElapsedChanged.connect(self._timeElapsedChanged)

    # Override
    @pyqtProperty(float, notify=_timeElapsedChanged)
    def progress(self) -> float:
        return self._progress

    def updateProgress(self, progress: float) -> None:
        self._progress = progress

    def getState(self) -> str:
        return self._state
