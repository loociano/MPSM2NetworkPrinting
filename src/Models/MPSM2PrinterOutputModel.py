# Copyright 2020 Luc Rubio <luc@loociano.com>
# Plugin is licensed under the GNU Lesser General Public License v3.0.
from cura.PrinterOutput.Models.PrinterOutputModel import PrinterOutputModel
from cura.PrinterOutput.PrinterOutputController import PrinterOutputController


class MPSM2PrinterOutputModel(PrinterOutputModel):
    def __init__(self, output_controller: PrinterOutputController) -> None:
        super().__init__(output_controller, number_of_extruders=1)

    def getPrinterState(self) -> str:
        return self._printer_state
