"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
import re
from typing import Optional

# pylint:disable=relative-beyond-top-level
from ..Models.MPSM2PrinterStatusModel import MPSM2PrinterStatusModel


class MPSM2PrinterStatusParser:
  """Parser for Monoprice Select Mini V2 HTTP status responses."""

  @staticmethod
  def parse(raw_response: str) -> Optional[MPSM2PrinterStatusModel]:
    """Parses the HTTP status response into a model.

    Args:
      raw_response: HTTP status body response.
    Returns:
      Model with printer state, temperatures and print progress.
    """
    matches = re.match(r"^T(\d+)/(\d+)P(\d+)/(\d+)/(\d+)([IP])$", raw_response)
    if matches is None:
      return None
    state = matches.group(6)
    return MPSM2PrinterStatusModel(
        hotend_temperature=int(matches.group(1)),
        target_hotend_temperature=int(matches.group(2)),
        bed_temperature=int(matches.group(3)),
        target_bed_temperature=int(matches.group(4)),
        progress=int(matches.group(5)),
        state=MPSM2PrinterStatusModel.State.IDLE if state == 'I'
        else
        MPSM2PrinterStatusModel.State.PRINTING if state == 'P'
        else
        MPSM2PrinterStatusModel.State.UNKNOWN)
