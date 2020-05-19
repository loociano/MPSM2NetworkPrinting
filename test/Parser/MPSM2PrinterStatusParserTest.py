# Copyright 2020 Luc Rubio <luc@loociano.com>
# Plugin is licensed under the GNU Lesser General Public License v3.0.
import unittest

from src.Models.MPSM2PrinterStatusModel import MPSM2PrinterStatusModel
from src.Parser.MPSM2PrinterStatusParser import MPSM2PrinterStatusParser


class MPSM2PrinterStatusParserTest(unittest.TestCase):
    def test_parses_whenPrinterIsIdle(self):
        model = MPSM2PrinterStatusParser.parse('T0/1P2/3/4I')
        self.assertEqual(model.hotend_temperature, 0)
        self.assertEqual(model.target_hotend_temperature, 1)
        self.assertEqual(model.bed_temperature, 2)
        self.assertEqual(model.target_bed_temperature, 3)
        self.assertEqual(model.progress, 4)
        self.assertEqual(model.state, MPSM2PrinterStatusModel.State.IDLE)

    def test_parses_whenPrinterIsPrinting(self):
        model = MPSM2PrinterStatusParser.parse('T120/210P50/60/55P')
        self.assertEqual(model.hotend_temperature, 120)
        self.assertEqual(model.target_hotend_temperature, 210)
        self.assertEqual(model.bed_temperature, 50)
        self.assertEqual(model.target_bed_temperature, 60)
        self.assertEqual(model.progress, 55)
        self.assertEqual(model.state, MPSM2PrinterStatusModel.State.PRINTING)

    def test_parse_withUnrecognizedFormat(self):
        self.assertIsNone(MPSM2PrinterStatusParser.parse('other format'))


if __name__ == '__main__':
    unittest.main()
