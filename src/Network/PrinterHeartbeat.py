# Copyright 2020 Luc Rubio <luc@loociano.com>
# Plugin is licensed under the GNU Lesser General Public License v3.0.
import time
from http.client import HTTPConnection

from PyQt5.QtCore import QThread, pyqtSignal


# Background thread that polls printer status. Status contains printer state, temperatures and printing progress.
class PrinterHeartbeat(QThread):
    REQUEST_TIMEOUT_SECS = 2
    POLL_INTERVAL_SECS = 5
    heartbeatSignal = pyqtSignal(str, str)  # address, raw response
    onPrinterUpload = pyqtSignal(bool)

    def __init__(self, parent=None) -> None:
        QThread.__init__(self, parent)
        self._printer_ip_address = None
        self.is_running = True

    def setPrinterIpAddress(self, printer_ip_address) -> None:
        self._printer_ip_address = printer_ip_address

    def handlePrinterBusy(self, is_uploading: bool) -> None:
        self.is_running = not is_uploading

    # Override
    def run(self) -> None:
        while True:
            if self.is_running:
                self._inquiry()
            time.sleep(PrinterHeartbeat.POLL_INTERVAL_SECS)

    def _inquiry(self) -> None:
        if self._printer_ip_address:
            connection = HTTPConnection(self._printer_ip_address, timeout=PrinterHeartbeat.REQUEST_TIMEOUT_SECS)
            try:
                connection.request('GET', '/inquiry')
                response = connection.getresponse()
                self.heartbeatSignal.emit(self._printer_ip_address, response.read().decode('utf-8'))
            except Exception:
                self.heartbeatSignal.emit(self._printer_ip_address, 'timeout')
            finally:
                connection.close()
