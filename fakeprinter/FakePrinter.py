"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
import logging
import socketserver
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

from typing import Tuple


class FakePrinter:
  """Emulates the Monoprice Select Mini V2 HTTP REST API."""

  def __init__(self):
    self._logger = logging.getLogger('FakePrinter')
    logging.basicConfig(level=logging.INFO)

  class Handler(BaseHTTPRequestHandler):
    """Handles HTTP requests."""
    printer = None

    def __init__(self, request: bytes, client_address: Tuple[str, int],
                 server: socketserver.BaseServer) -> None:
      """Constructor."""
      self._logger = logging.getLogger('FakePrinterHandler')
      super().__init__(request, client_address, server)

    # pylint:disable=invalid-name
    def do_GET(self) -> None:
      """Handles HTTP GET requests."""
      response = 'OK'
      if self.path == '/inquiry':
        response = 'T{}/{}P{}/{}/{}{}'.format(
            self.printer.hotend,
            self.printer.target_hotend,
            self.printer.bed,
            self.printer.target_bed,
            self.printer.progress,
            'I' if self.printer.state == 'idle' else 'P')
      elif self.path == '/set?cmd=%7BP:M%7D':  # print cached model
        time.sleep(2)
        self.printer.state = 'printing'
      elif self.path == '/set?cmd=%7BP:X%7D':  # cancel print
        time.sleep(2)
        self.printer.state = 'idle'
      else:
        self._send_not_found_headers()
        self.wfile.write('Not Found'.encode('utf-8'))
        return
      self._logger.info('Response: %s', response)
      self._send_success_headers()
      self.wfile.write(response.encode('utf-8'))

    def do_POST(self) -> None:
      """Handles HTTP POST requests."""
      if self.path == '/upload':
        self._send_success_headers()
        content_length = int(self.headers['Content-Length'])
        self.rfile.read(content_length)
        self.wfile.write('OK'.encode('utf-8'))
      else:
        self._send_not_found_headers()
        self.wfile.write('Not Found'.encode('utf-8'))

    def _send_success_headers(self):
      self.send_response(200)
      self.send_header('Content-type', 'text/html')
      self.end_headers()

    def _send_not_found_headers(self):
      self.send_response(404)
      self.send_header('Content-type', 'text/html')
      self.end_headers()

  def run(self, server_class=HTTPServer, handler_class=Handler) -> None:
    """Runs the fake printer."""
    server_address = ('', 80)
    self._logger.info('Starting fake printer on http://localhost:80')
    handler_class.printer = self.Printer()
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

  class Printer:
    def __init__(self):
      self.state = 'idle'
      self.hotend = 25
      self.target_hotend = 0
      self.bed = 20
      self.target_bed = 0
      self.progress = 0


if __name__ == '__main__':
  try:
    FakePrinter().run()
  except OSError:
    print(
        'On Windows: try disabling World Wide Web Publishing Service to use '
        'port 80.')
