# Copyright 2020 Luc Rubio <luc@loociano.com>
# Plugin is licensed under the GNU Lesser General Public License v3.0.
from typing import Callable, Tuple

from PyQt5.QtCore import QUrl
from PyQt5.QtNetwork import QNetworkReply, QHttpPart, QNetworkRequest, QHttpMultiPart, QNetworkAccessManager

from UM.Logger import Logger


class ApiClient:
    # In order to avoid garbage collection we keep the callbacks in this list.
    _anti_gc_callbacks = []

    def __init__(self, address: str, on_error: Callable) -> None:
        super().__init__()
        self._manager = QNetworkAccessManager()
        self._manager.finished.connect(self._handleOnFinished)
        self._address = address
        self._on_error = on_error
        self._upload_reply = None
        # QHttpMultiPart objects need to be kept alive and not garbage collected during the
        # HTTP which uses them. We hold references to these QHttpMultiPart objects here.
        self._cached_multiparts = {}

    def getPrinterStatus(self, on_finished: Callable) -> None:
        reply = self._manager.get(self._createEmptyRequest('/inquiry'))
        self._addCallback(reply, on_finished)

    def startPrint(self, on_finished: Callable = None) -> None:
        reply = self._manager.get(self._createEmptyRequest('/set?cmd={P:M}'))
        if on_finished:
            self._addCallback(reply, on_finished)

    def resumePrint(self, on_finished: Callable = None) -> None:
        reply = self._manager.get(self._createEmptyRequest('/set?cmd={P:R}'))
        self._addCallback(reply, on_finished)

    def pausePrint(self, on_finished: Callable = None) -> None:
        reply = self._manager.get(self._createEmptyRequest('/set?cmd={P:P}'))
        self._addCallback(reply, on_finished)

    def cancelPrint(self, on_finished: Callable = None) -> None:
        reply = self._manager.get(self._createEmptyRequest('/set?cmd={P:X}'))
        self._addCallback(reply, on_finished)

    def uploadPrint(self, filename: str, payload: bytes, on_finished: Callable, on_progress: Callable) -> None:
        http_part = QHttpPart()
        http_part.setHeader(QNetworkRequest.ContentDispositionHeader,
                            'form-data; name="file"; filename="{}"'.format(filename))
        http_part.setHeader(QNetworkRequest.ContentTypeHeader, 'application/octet-stream')
        http_part.setBody(payload)

        http_multi_part = QHttpMultiPart(QHttpMultiPart.FormDataType)
        http_multi_part.append(http_part)

        request = self._createEmptyRequest('/upload')
        # Must encode bytes boundary into string!
        request.setHeader(QNetworkRequest.ContentTypeHeader,
                          'multipart/form-data; boundary=%s' % str(http_multi_part.boundary(), 'utf-8'))

        reply = self._manager.post(request, http_multi_part)
        self._addCallback(reply, on_finished)
        self._anti_gc_callbacks.append(on_progress)
        reply.uploadProgress.connect(on_progress)
        self._cached_multiparts[reply] = http_multi_part  # prevent HTTP multi-part to be garbage-collected.
        self._upload_reply = reply # cache to cancel

    def cancelUploadPrint(self) -> None:
        Logger.log('d', 'Cancelling upload request.')
        if self._upload_reply:
            self._upload_reply.abort()

    def _handleOnFinished(self, reply: QNetworkReply) -> None:
        # Due to garbage collection, we need to cache certain bits of post operations.
        # As we don't want to keep them around forever, delete them if we get a reply.
        if reply.operation() == QNetworkAccessManager.PostOperation:
            self._clearCachedMultiPart(reply)

    def _clearCachedMultiPart(self, reply: QNetworkReply) -> None:
        if reply in self._cached_multiparts:
            del self._cached_multiparts[reply]

    def _createEmptyRequest(self, path: str) -> QNetworkRequest:
        url = QUrl('http://' + self._address + path)
        Logger.log('d', url.toString())
        request = QNetworkRequest(url)
        request.setAttribute(QNetworkRequest.FollowRedirectsAttribute, True)
        return request

    @staticmethod
    def _parseReply(reply: QNetworkReply) -> Tuple[int, str]:
        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        try:
            response = bytes(reply.readAll()).decode()
            return status_code, response
        except (UnicodeDecodeError, ValueError) as err:
            Logger.logException('e', 'Could not parse the printer response: %s', err)
            return status_code, err

    def _addCallback(self, reply: QNetworkReply, on_finished: Callable) -> None:
        def parse() -> None:
            self._anti_gc_callbacks.remove(parse)
            self._upload_reply = None

            if reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) is None or reply.error() > 0:
                Logger.log('e', 'No response received from printer.')
                return

            status_code, raw_response = self._parseReply(reply)
            on_finished(raw_response)

        self._anti_gc_callbacks.append(parse)
        reply.finished.connect(parse)
