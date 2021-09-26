"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
import re
from typing import Tuple


# TODO: convert Tuple to new class.
def parse(gcode: bytes) -> Tuple[int, int]:
  """Parses preheating bed and hotend temperature from gcode.

  Args:
    gcode: UTF-8 byte stream

  Returns:
    Tuple with preheat bed and hotend temperature. Both can be None.
  """
  bed_temperature, hotend_temperature = None, None

  for line in gcode.decode('utf-8').splitlines():
    if bed_temperature is not None and hotend_temperature is not None:
      return bed_temperature, hotend_temperature

    if bed_temperature is None:
      # M190 = Wait for bed temperature to reach target temperature.
      bed_match = re.match(r"^.*M190 S(\d+).*$", line)
      if bed_match is not None:
        bed_temperature = int(bed_match.group(1))

    if hotend_temperature is None:
      # M109 = Set Extruder Temperature and wait.
      hotend_match = re.match(r"^.*M109 S(\d+).*$", line)
      if hotend_match is not None:
        hotend_temperature = int(hotend_match.group(1))

  return bed_temperature, hotend_temperature
