"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
from typing import Callable

from PyQt5.QtCore import QUrl
from PyQt5.QtNetwork import QNetworkReply, QHttpPart, QNetworkRequest, \
  QHttpMultiPart, QNetworkAccessManager

from UM.Logger import Logger


class ApiClient:
  """Printer REST API client."""

  def __init__(self, address: str, on_error: Callable) -> None:
    super().__init__()
    self._manager = QNetworkAccessManager()
    self._manager.finished.connect(self._handle_on_finished)
    self._address = address
    self._on_error = on_error
    self._upload_reply = None
    # QHttpMultiPart objects need to be kept alive and not garbage collected
    # during the HTTP which uses them. We hold references to these
    # QHttpMultiPart objects here.
    self._cached_multiparts = {}

  def get_printer_status(self, on_finished: Callable) -> None:
    """Gets printer status. Status contains temperatures, printer state and
    progress if printing.

    Args:
      on_finished: callback after request completes.
    """
    reply = self._manager.get(self._create_empty_request('/inquiry'))
    self._add_callback(reply, on_finished)

  def start_print(self, on_finished: Callable = None) -> None:
    """Tells the printer to start printing.

    Args:
      on_finished: callback after request completes.
    """
    reply = self._manager.get(self._create_empty_request('/set?cmd={P:M}'))
    if on_finished:
      self._add_callback(reply, on_finished)

  def resume_print(self, on_finished: Callable = None) -> None:
    """Tells the printer to resume a paused print.
    If called when not paused, starts the print but the printer UI breaks.

    Args:
      on_finished: callback after request completes.
    """
    reply = self._manager.get(self._create_empty_request('/set?cmd={P:R}'))
    self._add_callback(reply, on_finished)

  def pause_print(self, on_finished: Callable = None) -> None:
    """Tells the printer to pause the print.
    If called when not printing, starts the print, pauses but the UI breaks.

    Args:
      on_finished: callback after request completes.
    """
    reply = self._manager.get(self._create_empty_request('/set?cmd={P:P}'))
    self._add_callback(reply, on_finished)

  def cancel_print(self, on_finished: Callable = None) -> None:
    """# Tells the printer to cancel the print.
    If called when not printing, it is a no-op.

    Args:
      on_finished: callback after request completes.
    """
    reply = self._manager.get(self._create_empty_request('/set?cmd={P:X}'))
    self._add_callback(reply, on_finished)

  def upload_print(self, filename: str, payload: bytes, on_finished: Callable,
                   on_progress: Callable) -> None:
    """Uploads a file to the printer with a POST multipart/form-data request.
    Args:
      filename: name of the file to upload
      payload: content in bytes
      on_finished: callback after request completes.
      on_progress: callback while file uploads.
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

    reply = self._manager.post(request, http_multi_part)
    self._add_callback(reply, on_finished)
    reply.uploadProgress.connect(on_progress)
    # Prevent HTTP multi-part to be garbage-collected.
    self._cached_multiparts[reply] = http_multi_part
    self._upload_reply = reply  # cache to cancel

  def cancel_upload_print(self) -> None:
    """Cancels the upload request."""
    Logger.log('d', 'Cancelling upload request.')
    if self._upload_reply:
      self._upload_reply.abort()

  def _handle_on_finished(self, reply: QNetworkReply) -> None:
    """Called when any previously issued HTTP request finishes.

    Args:
      reply: HTTP response
    """
    # Due to garbage collection, we need to cache certain bits of post
    # operations. As we don't want to keep them around forever, delete them if
    # we get a reply.
    if reply.operation() == QNetworkAccessManager.PostOperation:
      self._clear_cached_multi_part(reply)

  def _clear_cached_multi_part(self, reply: QNetworkReply) -> None:
    """Clears cached reply of a POST multipart/form-data request.

    Args:
      reply: HTTP response.
    """
    if reply in self._cached_multiparts:
      del self._cached_multiparts[reply]

  def _create_empty_request(self, path: str) -> QNetworkRequest:
    """"Creates an empty HTTP request (GET or POST).

    Args:
      path: HTTP relative path.
    """
    url = QUrl('http://' + self._address + path)
    Logger.log('d', url.toString())
    request = QNetworkRequest(url)
    request.setAttribute(QNetworkRequest.FollowRedirectsAttribute, True)
    return request

  def _add_callback(self, reply: QNetworkReply, on_finished: Callable) -> None:
    """Adds a callback to an HTTP request.

    Args:
      reply: HTTP response.
      on_finished: callback after request completes.
    """
    def parse() -> None:
      """Parses the HTTP response."""
      self._upload_reply = None

      if reply.attribute(
          QNetworkRequest.HttpStatusCodeAttribute) is None or reply.error() > 0:
        Logger.log('e', 'No response received from printer.')
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
      Logger.logException('e', 'Could not parse the printer response: %s', err)
      return err
