"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
import io
from typing import List, Optional

from UM.FileHandler.FileHandler import FileHandler
from UM.FileHandler.WriteFileJob import WriteFileJob
from UM.FileHandler.FileWriter import FileWriter
from UM.Scene.SceneNode import SceneNode

# pylint:disable=import-error
from cura.CuraApplication import CuraApplication


class GCodeWriteFileJob(WriteFileJob):
  """Represents a g-code write file job."""
  def __init__(self, file_handler: Optional[FileHandler],
               nodes: List[SceneNode]) -> None:
    # GCodeWriter only supports TextMode.
    super().__init__(file_handler.getWriterByMimeType('text/x-gcode'),
                     io.StringIO(), nodes,
                     FileWriter.OutputMode.TextMode)
    job_name = CuraApplication.getInstance().getPrintInformation().jobName
    self.setFileName(f'{job_name}.gcode')

  def get_gcode_output(self) -> bytes:
    """Produces a readable g-code output of the model.

    Returns:
      UTF-8 stream.
    """
    return self.getStream().getvalue().encode('utf-8')
