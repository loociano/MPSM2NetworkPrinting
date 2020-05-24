"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
import logging
import socketserver
from http.server import HTTPServer, BaseHTTPRequestHandler

from typing import Tuple


class FakePrinter:
  """Emulates the Monoprice Select Mini V2 HTTP REST API."""

  def __init__(self):
    self._logger = logging.getLogger('FakePrinter')
    logging.basicConfig(level=logging.INFO)

  class Handler(BaseHTTPRequestHandler):
    """Handles HTTP requests."""

    def __init__(self, request: bytes, client_address: Tuple[str, int],
                 server: socketserver.BaseServer) -> None:
      """Constructor."""
      self._logger = logging.getLogger('FakePrinterHandler')
      super().__init__(request, client_address, server)

    # pylint:disable=invalid-name
    def do_GET(self) -> None:
      """Handles HTTP GET requests."""
      self.send_response(200)
      self.send_header('Content-type', 'text/html')
      self.end_headers()
      if self.path == '/inquiry':
        response = 'T0/0P0/0/0I'
      else:
        response = 'OK'
      self._logger.info('Response: %s', response)
      self.wfile.write(response.encode('utf-8'))

  def run(self, server_class=HTTPServer, handler_class=Handler) -> None:
    """Runs the fake printer."""
    server_address = ('', 80)
    self._logger.info('Starting fake printer on http://localhost:80')
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


if __name__ == '__main__':
  try:
    FakePrinter().run()
  except OSError:
    print(
        'On Windows: try disabling World Wide Web Publishing Service to use '
        'port 80.')
