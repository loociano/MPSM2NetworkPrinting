"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
import re
from typing import Optional

from UM.Logger import Logger

# pylint:disable=relative-beyond-top-level
from ..models.MPSM2PrinterStatusModel import MPSM2PrinterStatusModel

_RESPONSE_STATUS_REGEX = r"^T(\d+)/(\d+)P(\d+)/(\d+)/(\d+)([IP])$"


def _to_model_state(state: str) -> MPSM2PrinterStatusModel.State:
  if state == 'I':
    return MPSM2PrinterStatusModel.State.IDLE
  if state == 'P':
    return MPSM2PrinterStatusModel.State.PRINTING
  return MPSM2PrinterStatusModel.State.UNKNOWN


def parse(raw_response: str) -> Optional[MPSM2PrinterStatusModel]:
  """Parses the HTTP status response into a model.

  Args:
    raw_response: HTTP status body response.
  Returns:
    Model with printer state, temperatures and print progress.
  """
  matches = re.match(_RESPONSE_STATUS_REGEX, raw_response)
  if not matches:
    Logger.log('e', 'Could not parse response: %s.', raw_response)
    return None
  return MPSM2PrinterStatusModel(
      hotend_temperature=int(matches.group(1)),
      target_hotend_temperature=int(matches.group(2)),
      bed_temperature=int(matches.group(3)),
      target_bed_temperature=int(matches.group(4)),
      progress=int(matches.group(5)),
      state=_to_model_state(matches.group(6)))
