# Copyright 2020 Luc Rubio <luc@loociano.com>
# Plugin is licensed under the GNU Lesser General Public License v3.0.
import re
from typing import Optional

from UM.Logger import Logger
from ..Models.MPSM2PrinterStatusModel import MPSM2PrinterStatusModel


class MPSM2PrinterStatusParser:
    @staticmethod
    def parse(raw_response: str) -> Optional[MPSM2PrinterStatusModel]:
        matches = re.match(r"^T(\d+)/(\d+)P(\d+)/(\d+)/(\d+)([IP])$", raw_response)
        if matches is None:
            return None
        state = matches.group(6)
        return MPSM2PrinterStatusModel(
            int(matches.group(1)),
            int(matches.group(2)),
            int(matches.group(3)),
            int(matches.group(4)),
            int(matches.group(5)),
            MPSM2PrinterStatusModel.State.IDLE if state == 'I'
            else
            MPSM2PrinterStatusModel.State.PRINTING if state == 'P'
            else
            MPSM2PrinterStatusModel.State.UNKNOWN)
