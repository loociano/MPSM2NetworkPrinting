"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
import enum


class MPSM2PrinterStatusModel:
  """Printer's Status Model."""

  class State(enum.Enum):
    """Printer State."""
    UNKNOWN = 1
    IDLE = 2
    PRINTING = 3

  def __init__(self, hotend_temperature: int, target_hotend_temperature: int,
               bed_temperature: int, target_bed_temperature: int, progress: int,
               state: State) -> None:
    """Constructor.

    Args:
      hotend_temperature: from 0 to 280.
      target_hotend_temperature: from 0 to 280.
      bed_temperature: from 0 to 85.
      target_bed_temperature: from 0 to 85.
      progress: from 0 to 100
      state: idle or printing.
    """
    self.hotend_temperature = hotend_temperature
    self.target_hotend_temperature = target_hotend_temperature
    self.bed_temperature = bed_temperature
    self.target_bed_temperature = target_bed_temperature
    self.progress = progress
    self.state = state
