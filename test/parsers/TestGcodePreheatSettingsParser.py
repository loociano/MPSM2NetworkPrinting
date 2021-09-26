"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
import unittest

from src.parsers import GcodePreheatSettingsParser


class GcodePreheatSettingsParserTest(unittest.TestCase):
  def test_parseBedAndHotendTemperature_success(self):
    gcode = """
    ;FLAVOR:Marlin
    M140 S65
    M105
    M190 S65
    M104 S205
    M105
    M109 S205 ;a comment
    M82"""
    self.assertTupleEqual(
        (65, 205), GcodePreheatSettingsParser.parse(str.encode(gcode)))

  def test_parseOnlyPreheatBedTemperature_success(self):
    gcode = """
    M190 S65
    M190 S0
    """
    self.assertTupleEqual(
        (65, None), GcodePreheatSettingsParser.parse(str.encode(gcode)))

  def test_parseOnlyPreheatHotendTemperature_success(self):
    gcode = """
    M109 S200
    M109 S0
    """
    self.assertTupleEqual(
        (None, 200), GcodePreheatSettingsParser.parse(str.encode(gcode)))

  def test_parseWithoutPreheatCommands_empty(self):
    self.assertTupleEqual(
        (None, None), GcodePreheatSettingsParser.parse(str.encode('M82')))

  def test_parseNoInput_empty(self):
    self.assertTupleEqual(
        (None, None), GcodePreheatSettingsParser.parse(str.encode('')))
