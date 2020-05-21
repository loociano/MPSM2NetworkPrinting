"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
from cura.PrinterOutput.Models.PrintJobOutputModel import PrintJobOutputModel
from cura.PrinterOutput.PrinterOutputController import PrinterOutputController
from cura.PrinterOutput.PrinterOutputDevice import PrinterOutputDevice


class MPSM2OutputController(PrinterOutputController):

  def __init__(self, output_device: PrinterOutputDevice) -> None:
    """Constructor.

    Args:
      output_device: printer output device.
    """
    super().__init__(output_device)
    self.can_pause = True
    self.can_abort = True
    self.can_pre_heat_bed = True
    self.can_pre_heat_hotends = True
    self.can_send_raw_gcode = True
    self.can_control_manually = True
    self.can_update_firmware = False

  # pylint:disable=invalid-name
  def setJobState(self, job: PrintJobOutputModel, state: str) -> None:
    """Sets job state.

    Args:
      job: print job output model.
      state: print job state.
    """
    self._output_device.setJobState(job.key, state)
