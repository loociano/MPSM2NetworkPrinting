"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
import enum


class MPSM2PrinterStatusModel:
  """Printer's Status Model."""

  MAX_HOTEND_TEMPERATURE = 260  # Degrees Celsius.
  MAX_BED_TEMPERATURE = 85  # Degrees Celsius.

  class State(enum.Enum):
    """Printer State."""
    UNKNOWN = enum.auto()
    IDLE = enum.auto()
    PRINTING = enum.auto()

  def __init__(self,
               hotend_temperature: int = 0,
               target_hotend_temperature: int = 0,
               bed_temperature: int = 0,
               target_bed_temperature: int = 0,
               progress: int = 0,
               state: State = State.IDLE) -> None:
    """Constructor.

    Args:
      hotend_temperature: From 0 to 260 degrees Celsius.
      target_hotend_temperature: From 0 to 260 degrees Celsius.
      bed_temperature: From 0 to 85 degrees Celsius.
      target_bed_temperature: From 0 to 85 degrees Celcsius.
      progress: print progress percentage, from 0 to 100.
      state: state the printer is in (e.g. idle, printing).
    """
    if (hotend_temperature < 0
        or hotend_temperature > self.MAX_HOTEND_TEMPERATURE):
      raise ValueError(f'Invalid hotend temperature: {hotend_temperature}.')
    if (target_hotend_temperature < 0
        or target_hotend_temperature > self.MAX_HOTEND_TEMPERATURE):
      raise ValueError(
          f'Invalid target hotend temperature: {target_hotend_temperature}.')
    if (bed_temperature < 0
        or bed_temperature > self.MAX_BED_TEMPERATURE):
      raise ValueError(f'Invalid bed temperature: {bed_temperature}.')
    if (target_bed_temperature < 0
        or target_bed_temperature > self.MAX_BED_TEMPERATURE):
      raise ValueError(
          f'Invalid target bed temperature: {target_bed_temperature}')
    if progress < 0 or progress > 100:
      raise ValueError(f'Invalid printing progress: {progress}.')
    self.hotend_temperature = hotend_temperature
    self.target_hotend_temperature = target_hotend_temperature
    self.bed_temperature = bed_temperature
    self.target_bed_temperature = target_bed_temperature
    self.progress = progress
    self.state = state
