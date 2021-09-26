"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
from typing import Callable, Optional

from PyQt5.QtCore import QUrl
from PyQt5.QtNetwork import QNetworkReply, QHttpPart, QNetworkRequest, QHttpMultiPart, QNetworkAccessManager

from UM.Logger import Logger

_MAX_TARGET_HOTEND_TEMPERATURE = 260
_MAX_TARGET_BED_TEMPERATURE = 85

class ApiClient:
  """Monoprice Select Mini REST API client."""

  def __init__(self, ip_address: str) -> None:
    """Constructor.

    Args:
      ip_address: Printer's IP address.
    """
    super().__init__()
    self._network_manager = QNetworkAccessManager()
    self._ip_address = ip_address
    self._upload_model_reply = None

  def get_printer_status(self, on_finished: Callable,
                         on_error: Callable) -> None:
    """Gets printer status.

    Status contains temperatures, printer state and progress if printing.

    Args:
      on_finished: Callback after request completes.
      on_error: Callback if the request fails.
    """
    reply = self._network_manager.get(self._create_empty_request('/inquiry'))
    self._register_callback(reply, on_finished, on_error)

  def increase_upload_speed(
      self, on_finished: Callable, on_error: Callable) -> None:
    """Tells the printer to increase the upload speed to 91 Kbps.

    Args:
      on_finished: Callback after request completes.
      on_error: Callback if the request fails.
    """
    # Default upload speed is 39 Kbps (level 2).
    # Monoprice Select Mini V2 supports 91 Kbps (level 4).
    # Source: https://github.com/nokemono42/MP-Select-Mini-Web
    reply = self._network_manager.get(
        self._create_empty_request('/set?code=M563%20S4'))
    self._register_callback(reply, on_finished, on_error)

  def start_print(self, on_finished: Optional[Callable] = None,
                  on_error=None) -> None:
    """Tells the printer to start printing.

    Args:
      on_finished: Callback after request completes.
      on_error: Callback if the request fails.
    """
    reply = self._network_manager.get(
        self._create_empty_request('/set?cmd={P:M}'))
    if on_finished is not None:
      self._register_callback(reply, on_finished, on_error)

  def resume_print(self, on_finished: Callable, on_error=None) -> None:
    """Tells the printer to resume a paused print.

    If called when not paused, starts the print but the printer UI breaks.

    Args:
      on_finished: Callback after request completes.
      on_error: Callback if the request fails.
    """
    reply = self._network_manager.get(
        self._create_empty_request('/set?cmd={P:R}'))
    self._register_callback(reply, on_finished, on_error)

  def pause_print(self, on_finished: Callable, on_error: Callable) -> None:
    """Tells the printer to pause the print.

    If called when not printing, starts the print, pauses but the UI breaks.

    Args:
      on_finished: Callback after request completes.
      on_error: Callback if the request fails.
    """
    reply = self._network_manager.get(
        self._create_empty_request('/set?cmd={P:P}'))
    self._register_callback(reply, on_finished, on_error)

  def cancel_print(self, on_finished: Optional[Callable] = None,
                   on_error=None) -> None:
    """Tells the printer to cancel the print.

    If called when not printing, it is a no-op.

    Args:
      on_finished: callback after request completes.
      on_error: callback if the request fails.
    """
    reply = self._network_manager.get(
        self._create_empty_request('/set?cmd={P:X}'))
    if on_finished is not None:
      self._register_callback(reply, on_finished, on_error)

  def upload_print(self, filename: str, payload: bytes, on_finished: Callable,
                   on_progress: Callable, on_error: Callable) -> None:
    """Uploads a file to the printer with a POST multipart/form-data request.

    Args:
      filename: Name of the file to upload
      payload: Content in bytes
      on_finished: Callback after request completes.
      on_progress: Callback while file uploads.
      on_error: Callback if the request fails.
    """
    http_part = QHttpPart()
    http_part.setHeader(QNetworkRequest.ContentDispositionHeader,
                        'form-data; name="file"; filename="{}"'.format(
                            filename))
    http_part.setHeader(QNetworkRequest.ContentTypeHeader,
                        'application/octet-stream')
    http_part.setBody(payload)

    http_multi_part = QHttpMultiPart(QHttpMultiPart.FormDataType)
    http_multi_part.append(http_part)

    request = self._create_empty_request('/upload')
    # Must encode bytes boundary into string!
    request.setHeader(QNetworkRequest.ContentTypeHeader,
                      'multipart/form-data; boundary=%s' % str(
                          http_multi_part.boundary(), 'utf-8'))

    reply = self._network_manager.post(request, http_multi_part)
    # Upload is special: on_error is connected directly on reply.error
    self._register_callback(reply, on_finished, None)
    reply.uploadProgress.connect(on_progress)
    reply.error.connect(on_error)
    # Prevent HTTP multi-part to be garbage-collected.
    http_multi_part.setParent(reply)
    self._upload_model_reply = reply  # cache to cancel

  def cancel_upload_print(self) -> None:
    """Cancels the upload request."""
    Logger.log('d', 'Cancelling upload request.')
    if self._upload_model_reply is not None:
      self._upload_model_reply.abort()
      self._upload_model_reply = None

  def set_target_hotend_temperature(self,
                                    celsius: int,
                                    on_finished: Callable,
                                    on_error: Callable) -> None:
    """Tells the printer the target hotend temperature.

    Args:
      celsius: Target hotend temperature
      on_finished: Callback after request completes.
      on_error: Callback if the request fails.
    """
    if celsius < 0 or celsius > _MAX_TARGET_HOTEND_TEMPERATURE:
      Logger.log('e', 'Target hotend temperature out of range.')
      return
    reply = self._network_manager.get(
        self._create_empty_request('/set?cmd={{C:T{:04d}}}'.format(celsius)))
    self._register_callback(reply, on_finished, on_error)

  def set_target_bed_temperature(self,
                                 celsius: int,
                                 on_finished: Callable,
                                 on_error: Callable) -> None:
    """Requests the printer to set a target bed temperature.

    Args:
      celsius: Target bed temperature
      on_finished: Callback after request completes.
      on_error: Callback if the request fails.
    """
    if celsius < 0 or celsius > _MAX_TARGET_BED_TEMPERATURE:
      Logger.log('e', 'Target bed temperature out of range.')
      return
    reply = self._network_manager.get(
        self._create_empty_request('/set?cmd={{C:P{:03d}}}'.format(celsius)))
    self._register_callback(reply, on_finished, on_error)

  def _create_empty_request(self, path: str) -> QNetworkRequest:
    """"Creates an empty HTTP request (GET or POST).

    Args:
      path: HTTP relative path.
    """
    url = QUrl('http://' + self._ip_address + path)
    Logger.log('d', url.toString())
    request = QNetworkRequest(url)
    request.setAttribute(QNetworkRequest.FollowRedirectsAttribute, True)
    return request

  def _register_callback(self, reply: QNetworkReply, on_finished: Callable,
                         on_error: Optional[Callable]) -> None:
    """Adds a callback to an HTTP request.

    Args:
      reply: HTTP response.
      on_finished: Callback after request completes.
      on_error: Callback on network error or timeout.
    """

    def parse() -> None:
      """Parses the HTTP response."""
      if reply.attribute(
          QNetworkRequest.HttpStatusCodeAttribute) is None or reply.error() > 0:
        Logger.log('e', 'No response received from printer.')
        if on_error is not None:
          on_error()
        return
      on_finished(self._parse_reply(reply))

    reply.finished.connect(parse)

  @staticmethod
  def _parse_reply(reply: QNetworkReply) -> str:
    """Parses the HTTP body response into string.

    Args:
      reply: HTTP response.
    """
    try:
      return bytes(reply.readAll()).decode()
    except (UnicodeDecodeError, ValueError) as err:
      Logger.logException('e', 'Could not parse the printer response: %s.', err)
      return err
