"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
from typing import Callable, List, Optional

USE_QT5 = False
try:
  # Cura 5.0.0+.
  from PyQt6.QtCore import QUrl
  from PyQt6.QtNetwork import QNetworkReply, QHttpPart, QNetworkRequest, QHttpMultiPart, QNetworkAccessManager
  QNetworkAccessManagerOperations = QNetworkAccessManager.Operation
except ImportError:
  # Cura 4.9.1 or older.
  from PyQt5.QtCore import QUrl
  from PyQt5.QtNetwork import QNetworkReply, QHttpPart, QNetworkRequest, QHttpMultiPart, QNetworkAccessManager
  QNetworkAccessManagerOperations = QNetworkAccessManager
  USE_QT5 = True

from UM.Logger import Logger

from ..models.MPSM2PrinterStatusModel import MPSM2PrinterStatusModel

MAX_TARGET_HOTEND_TEMPERATURE = MPSM2PrinterStatusModel.MAX_TARGET_HOTEND_TEMPERATURE
MAX_TARGET_BED_TEMPERATURE = MPSM2PrinterStatusModel.MAX_TARGET_BED_TEMPERATURE


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
    # Prevent auto-removing running callbacks by the Python garbage collector.
    self._anti_gc_callbacks: List[Callable[[], None]] = []

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
      self._anti_gc_callbacks.remove(parse)
      if USE_QT5:
        http_status_code_attribute = QNetworkRequest.HttpStatusCodeAttribute
        has_error = reply.error() > 0
      else:
        http_status_code_attribute = QNetworkRequest.Attribute.HttpStatusCodeAttribute
        has_error = reply.error() != QNetworkReply.NetworkError.NoError
      if reply.attribute(http_status_code_attribute) is None or has_error:
        Logger.log('e', 'No response received from printer.')
        if on_error:
          on_error()
        return
      on_finished(_parse_reply(reply))

    self._anti_gc_callbacks.append(parse)
    reply.finished.connect(parse)

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
    if on_finished:
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
    if on_finished:
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
    if USE_QT5:
      content_disposition_header = QNetworkRequest.ContentDispositionHeader
      content_type_header = QNetworkRequest.ContentTypeHeader
      form_data_type = QHttpMultiPart.FormDataType
    else:
      content_disposition_header = QNetworkRequest.KnownHeaders.ContentDispositionHeader
      content_type_header = QNetworkRequest.KnownHeaders.ContentTypeHeader
      form_data_type = QHttpMultiPart.ContentType.FormDataType
    http_part = QHttpPart()
    http_part.setHeader(content_disposition_header,
                        f'form-data; name="file"; filename="{filename}"')
    http_part.setHeader(content_type_header, 'application/octet-stream')
    http_part.setBody(payload)

    http_multi_part = QHttpMultiPart(form_data_type)
    http_multi_part.append(http_part)

    request = self._create_empty_request('/upload')
    # Must encode bytes boundary into string!
    bytes_boundary = str(http_multi_part.boundary(), 'utf-8')
    request.setHeader(content_type_header,
                      f'multipart/form-data; boundary={bytes_boundary}')

    reply = self._network_manager.post(request, http_multi_part)
    # Upload is special: on_error is connected directly on reply.error
    self._register_callback(reply, on_finished, None)
    reply.uploadProgress.connect(on_progress)
    if USE_QT5:
      reply.error.connect(on_error)
    else:
      reply.errorOccurred.connect(on_error)
    # Prevent HTTP multi-part to be garbage-collected.
    http_multi_part.setParent(reply)
    self._upload_model_reply = reply  # Cache to cancel.

  def cancel_upload_print(self) -> None:
    """Cancels the upload request."""
    Logger.log('d', 'Cancelling upload request.')
    if self._upload_model_reply:
      self._upload_model_reply.abort()
      self._upload_model_reply = None

  def set_target_hotend_temperature(self,
                                    temperature: int,
                                    on_finished: Callable,
                                    on_error: Callable) -> None:
    """Tells the printer the target hotend temperature.

    Args:
      temperature: Target hotend temperature.
      on_finished: Callback after request completes.
      on_error: Callback if the request fails.
    """
    if temperature < 0 or temperature > MAX_TARGET_HOTEND_TEMPERATURE:
      Logger.log('e', 'Target hotend temperature out of range.')
      return
    reply = self._network_manager.get(
        self._create_empty_request(f'/set?cmd={{C:T{temperature:04d}}}'))
    self._register_callback(reply, on_finished, on_error)

  def set_target_bed_temperature(self,
                                 temperature: int,
                                 on_finished: Callable,
                                 on_error: Callable) -> None:
    """Requests the printer to set a target bed temperature.

    Args:
      temperature: Target bed temperature.
      on_finished: Callback after request completes.
      on_error: Callback if the request fails.
    """
    if temperature < 0 or temperature > MAX_TARGET_BED_TEMPERATURE:
      Logger.log('e', 'Target bed temperature out of range.')
      return
    reply = self._network_manager.get(
        self._create_empty_request(f'/set?cmd={{C:P{temperature:03d}}}'))
    self._register_callback(reply, on_finished, on_error)

  def _create_empty_request(self, path: str) -> QNetworkRequest:
    """"Creates an empty HTTP request (GET or POST).

    Args:
      path: HTTP relative path.
    """
    url = QUrl(f'http://{self._ip_address}{path}')
    Logger.log('d', url.toString())
    request = QNetworkRequest(url)
    if USE_QT5:
      request.setAttribute(QNetworkRequest.FollowRedirectsAttribute, True)
    else:
      # FollowRedirectsAttribute was deprecated in PyQt6.
      # https://doc.qt.io/qt-6/network-changes-qt6.html#redirect-policies.
      request.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute,
                           QNetworkRequest.RedirectPolicy.ManualRedirectPolicy)
    return request
