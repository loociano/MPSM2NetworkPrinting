"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
import time
from http.client import HTTPConnection

try:
  # Cura 5.0.0+.
  from PyQt6.QtCore import QThread, pyqtSignal
except ImportError:
  # Cura 4.9.1 or older.
  from PyQt5.QtCore import QThread, pyqtSignal


_REQUEST_TIMEOUT_SECS = 2
_POLL_INTERVAL_SECS = 2


class PrinterHeartbeat(QThread):
  """
  Background thread that polls printer status.

  Status contains printer state, temperatures and printing progress.
  """
  heartbeatSignal = pyqtSignal(str, str)  # Address, raw response.
  onPrinterUpload = pyqtSignal(bool)

  def __init__(self, address: str, parent=None) -> None:
    QThread.__init__(self, parent)
    self._address = address
    self._is_running = True
    self._is_uploading = False

  def handle_printer_busy(self, is_uploading: bool) -> None:
    self._is_uploading = is_uploading

  def stopBeat(self):
    self._is_running = False

  def run(self) -> None:
    """See base class."""
    while self._is_running:
      if not self._is_uploading:
        self._inquiry()
      time.sleep(_POLL_INTERVAL_SECS)

  def _inquiry(self) -> None:
    """Queries printer status."""
    connection = HTTPConnection(self._address, timeout=_REQUEST_TIMEOUT_SECS)
    try:
      connection.request('GET', '/inquiry')
      response = connection.getresponse()
      self.heartbeatSignal.emit(self._address,
                                response.read().decode('utf-8'))
    except Exception:
      self.heartbeatSignal.emit(self._address, 'timeout')
    finally:
      connection.close()
