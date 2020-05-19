# Copyright 2020 Luc Rubio <luc@loociano.com>
# Plugin is licensed under the GNU Lesser General Public License v3.0.
import io
from typing import List, Optional

from UM.FileHandler.FileHandler import FileHandler
from UM.FileHandler.WriteFileJob import WriteFileJob
from UM.FileHandler.FileWriter import FileWriter
from UM.Scene.SceneNode import SceneNode

from cura.CuraApplication import CuraApplication


class GCodeWriteFileJob(WriteFileJob):
    def __init__(self, file_handler: Optional[FileHandler], nodes: List[SceneNode]) -> None:
        super().__init__(file_handler.getWriterByMimeType('text/x-gcode'), io.StringIO(), nodes,
                         FileWriter.OutputMode.TextMode) # GCodeWriter only supports TextMode
        self.setFileName('{}.gcode'.format(CuraApplication.getInstance().getPrintInformation().jobName))

    def getGcodeOutput(self) -> bytes:
        return self.getStream().getvalue().encode('utf-8')
