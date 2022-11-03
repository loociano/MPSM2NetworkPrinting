"""
Copyright 2021 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
import unittest

from src.models.MPSM2PrinterStatusModel import MPSM2PrinterStatusModel


class MPSM2PrinterStatusModelTest(unittest.TestCase):
  def test_invalidHotendTemperature_fails(self):
    with self.assertRaises(ValueError):
      MPSM2PrinterStatusModel(hotend_temperature=-1)

  def test_invalidTargetHotendTemperature_fails(self):
    with self.assertRaises(ValueError):
      MPSM2PrinterStatusModel(target_hotend_temperature=-1)

  def test_invalidBedTemperature_fails(self):
    with self.assertRaises(ValueError):
      MPSM2PrinterStatusModel(bed_temperature=-1)

  def test_invalidTargetBedTemperature_fails(self):
    with self.assertRaises(ValueError):
      MPSM2PrinterStatusModel(target_bed_temperature=-1)

  def test_invalidProgress_fails(self):
    with self.assertRaises(ValueError):
      MPSM2PrinterStatusModel(progress=-1)
    with self.assertRaises(ValueError):
      MPSM2PrinterStatusModel(progress=101)
