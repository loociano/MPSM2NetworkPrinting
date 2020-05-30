"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
from cura.PrinterOutput.Models.PrinterOutputModel import PrinterOutputModel
from cura.PrinterOutput.PrinterOutputController import PrinterOutputController


class MPSM2PrinterOutputModel(PrinterOutputModel):
  """Printer's output model."""

  def __init__(self, output_controller: PrinterOutputController) -> None:
    """Constructor.

    Args:
      output_controller: printer's output controller.
    """
    super().__init__(output_controller, number_of_extruders=1)

  def get_printer_state(self) -> str:
    """
    Returns:
      Printer state. Can be 'idle' or 'printing'.
    """
    return self._printer_state
