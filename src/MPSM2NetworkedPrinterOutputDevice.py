# Copyright 2020 Luc Rubio <luc@loociano.com>
# Plugin is licensed under the GNU Lesser General Public License v3.0.
import os
from typing import List, Optional, Dict

from PyQt5.QtCore import pyqtProperty, pyqtSignal, QObject, pyqtSlot

from UM.FileHandler.FileHandler import FileHandler
from UM.Logger import Logger
from UM.i18n import i18nCatalog
from UM.Scene.SceneNode import SceneNode

from cura.CuraApplication import CuraApplication
from cura.PrinterOutput.Models.ExtruderConfigurationModel import ExtruderConfigurationModel
from cura.PrinterOutput.Models.PrinterConfigurationModel import PrinterConfigurationModel
from cura.PrinterOutput.Models.PrinterOutputModel import PrinterOutputModel
from cura.PrinterOutput.NetworkedPrinterOutputDevice import NetworkedPrinterOutputDevice, AuthState
from cura.PrinterOutput.PrinterOutputDevice import ConnectionType, ConnectionState

from .MPSM2OutputController import MPSM2OutputController
from .Models.MPSM2PrinterOutputModel import MPSM2PrinterOutputModel
from .Models.MPSM2PrinterStatusModel import MPSM2PrinterStatusModel
from .Models.MPSM2PrintJobOutputModel import MPSM2PrintJobOutputModel
from .Network.ApiClient import ApiClient
from .GCodeWriteFileJob import GCodeWriteFileJob
from .Messages.PrintJobUploadProgressMessage import PrintJobUploadProgressMessage
from .Messages.PrintJobUploadBlockedMessage import PrintJobUploadBlockedMessage
from .Messages.PrintJobUploadSuccessMessage import PrintJobUploadSuccessMessage
from .Messages.PrintJobUploadCancelMessage import PrintJobUploadCancelMessage
from .Messages.PrintJobUploadIsPrintingMessage import PrintJobUploadIsPrintingMessage
from .Parser.MPSM2PrinterStatusParser import MPSM2PrinterStatusParser

I18N_CATALOG = i18nCatalog('cura')


class MPSM2NetworkedPrinterOutputDevice(NetworkedPrinterOutputDevice):
    META_NETWORK_KEY = 'mpsm2_network_key'

    printerStatusChanged = pyqtSignal()
    onPrinterUpload = pyqtSignal(bool)

    def __init__(self, device_id: str, address: str, properties: Dict[bytes, bytes], connection_type: ConnectionType,
                 parent=None) -> None:
        super().__init__(device_id=device_id, address=address, properties=properties, connection_type=connection_type,
                         parent=parent)
        self._printer_output_controller = MPSM2OutputController(self)
        self._printer_raw_response = ''  # HTTP string response body
        self._is_busy = False

        # Set the display name from the properties.
        self.setName(self.getProperty('name'))

        # Set the display name of the printer type.
        definitions = CuraApplication.getInstance().getContainerRegistry().findContainers(id=self.printerType)
        self._printer_type_name = definitions[0].getName() if definitions else ''
        self._job_upload_message = PrintJobUploadProgressMessage(self._onPrintUploadCancelled)
        self._api_client = ApiClient(self.address, on_error=lambda error: Logger.log('e', str(error)))

        self._print_job_model = MPSM2PrintJobOutputModel(self._printer_output_controller)
        self._printer_output_model = self._buildPrinterOutputModel()  # type: MPSM2PrinterOutputModel

        self.setAuthenticationState(AuthState.Authenticated)
        self._loadMonitorTab()
        self._setInterfaceElements()

    # Produces main object for rendering the Printer Monitor tab.
    @pyqtProperty(QObject, notify=printerStatusChanged)
    def printer(self) -> PrinterOutputModel:
        if self._printer_raw_response.upper() != 'OK':
            self._onPrinterStatusChanged(self._printer_raw_response)
        else:
            Logger.log('d', self._printer_output_model.extruders[0].__dict__)
        return self._printer_output_model

    @pyqtSlot(name='startPrint')
    def startPrint(self) -> None:
        Logger.log('d', 'Printing cache.gc.')
        self._api_client.startPrint(self._onPrintStarted)

    @pyqtSlot(name='pauseOrResumePrint')
    def pauseOrResumePrint(self) -> None:
        if self._print_job_model.getState() == 'paused':
            Logger.log('d', 'Resuming print.')
            self._api_client.resumePrint(self._onPrintResumed)
        else:
            Logger.log('d', 'Pausing print.')
            self._api_client.pausePrint(self._onPrintPaused)

    @pyqtSlot(name='cancelPrint')
    def cancelPrint(self) -> None:
        Logger.log('d', 'Cancelling print.')
        self._api_client.cancelPrint(self._onPrintCancelled)

    # Override
    def connect(self) -> None:
        Logger.log('d', 'Connecting.')
        super().connect()
        self._update()

    # Override
    def close(self) -> None:
        Logger.log('d', 'Closing.')
        super().close()
        self.setConnectionState(ConnectionState.Closed)
        if self.key in CuraApplication.getInstance().getOutputDeviceManager().getOutputDeviceIds():
            CuraApplication.getInstance().getOutputDeviceManager().removeOutputDevice(self.key)

    # Override
    def requestWrite(self, nodes: List[SceneNode], file_name: Optional[str] = None, limit_mimetypes: bool = False,
                     file_handler: Optional[FileHandler] = None, filter_by_machine: bool = False, **kwargs) -> None:
        Logger.log('d', 'Write to Output Device was requested.')
        if self._job_upload_message.visible:
            PrintJobUploadBlockedMessage().show()
            return
        if self._printer_output_model.getPrinterState() == 'printing':
            PrintJobUploadIsPrintingMessage().show()
            return

        self.writeStarted.emit(self)
        job = GCodeWriteFileJob(file_handler=file_handler, nodes=nodes)
        job.finished.connect(self._onPrintJobCreated)
        job.start()

    def updatePrinterStatus(self, raw_response: str) -> None:
        self._printer_raw_response = raw_response

    def isBusy(self) -> bool:
        return self._is_busy

    def _onPrintJobCreated(self, job: GCodeWriteFileJob) -> None:
        if not job:
            Logger.log('e', 'No active exported job to upload!')
            return
        self.onPrinterUpload.emit(True)
        self._is_busy = True
        self._job_upload_message.show()
        self._api_client.uploadPrint(job.getFileName(), job.getGcodeOutput(), self._onPrintUploadCompleted,
                                     self._onPrintJobUploadProgress)

    def _onPrintUploadCancelled(self) -> None:
        self._is_busy = False
        self._job_upload_message.hide()
        self._api_client.cancelUploadPrint()
        PrintJobUploadCancelMessage().show()
        self.writeFinished.emit()
        self.onPrinterUpload.emit(False)

    def _onPrintUploadCompleted(self) -> None:
        self._is_busy = False
        self._job_upload_message.hide()
        PrintJobUploadSuccessMessage().show()
        self._api_client.startPrint()  # force start
        self.writeFinished.emit()
        self.onPrinterUpload.emit(False)

    def _onPrintJobUploadProgress(self, bytes_sent: int, bytes_total: int) -> None:
        percentage = (bytes_sent / bytes_total) if bytes_total else 0
        self._job_upload_message.setProgress(percentage * 100)
        self.writeProgress.emit()

    def _onPrintStarted(self, raw_response: str) -> None:
        self._onPrintResumed(raw_response)

    def _onPrintResumed(self, raw_response: str) -> None:
        self._printer_raw_response = raw_response
        if raw_response.upper() == 'OK':
            self._printer_output_model.updateState('printing')
            self._print_job_model.updateState('active')
            self.printerStatusChanged.emit()
        else:
            Logger.log('d', 'Could not resume print')  # TODO message

    def _onPrintPaused(self, raw_response: str) -> None:
        self._printer_raw_response = raw_response
        if raw_response.upper() == 'OK':
            self._printer_output_model.updateState('paused')
            self._print_job_model.updateState('paused')
            self.printerStatusChanged.emit()
        else:
            Logger.log('d', 'Could not pause print')  # TODO: message

    def _onPrintCancelled(self, raw_response: str) -> None:
        self._printer_raw_response = raw_response
        if raw_response.upper() == 'OK':
            self._printer_output_model.updateState('idle')
            self._print_job_model.updateState('not_started')
            self._print_job_model.updateProgress(0)
            self.printerStatusChanged.emit()
        else:
            Logger.log('d', 'Could not cancel print')  # TODO: message

    def _setInterfaceElements(self) -> None:
        self.setPriority(3)  # Make sure the output device gets selected above local file output
        self.setShortDescription(I18N_CATALOG.i18nc('@action:button Preceded by "Ready to".', 'Print over network'))
        self.setDescription(I18N_CATALOG.i18nc('@properties:tooltip', 'Print over network'))
        self.setConnectionText(I18N_CATALOG.i18nc('@info:status', 'Connected over the network'))

    def _loadMonitorTab(self) -> None:
        plugin_registry = CuraApplication.getInstance().getPluginRegistry()
        if not plugin_registry:
            Logger.log('e', 'Could not get plugin registry.')
            return
        plugin_path = plugin_registry.getPluginPath('MPSM2NetworkPrinting')
        if not plugin_path:
            Logger.log('e', 'Could not get plugin path.')
            return
        self._monitor_view_qml_path = os.path.join(plugin_path, 'resources', 'qml', 'MonitorStage.qml')

    def _buildPrinterOutputModel(self) -> MPSM2PrinterOutputModel:
        printer_output_model = MPSM2PrinterOutputModel(self._printer_output_controller)
        printer_output_model.updateKey(self._address)
        printer_output_model.updateName(self.address)
        printer_output_model.updateState('idle')
        printer_output_model.setAvailableConfigurations([self._buildPrinterConfigurationModel()])
        printer_output_model.updateType('Monoprice Select Mini')
        printer_output_model.updateActivePrintJob(self._print_job_model)
        return printer_output_model

    def _buildExtruderConfigurationModel(self) -> ExtruderConfigurationModel:
        extruder_conf_model = ExtruderConfigurationModel()
        extruder_conf_model.setPosition(0)
        return extruder_conf_model

    def _buildPrinterConfigurationModel(self) -> PrinterConfigurationModel:
        printer_configuration_model = PrinterConfigurationModel()
        printer_configuration_model.setExtruderConfigurations([self._buildExtruderConfigurationModel()])
        printer_configuration_model.setPrinterType('type')
        return printer_configuration_model

    def _onPrinterStatusChanged(self, raw_response: str) -> None:
        printer_status_model = MPSM2PrinterStatusParser.parse(raw_response)
        if printer_status_model:
            self._printer_output_model.extruders[0].updateHotendTemperature(
                float(printer_status_model.hotend_temperature))
            self._printer_output_model.extruders[0].updateTargetHotendTemperature(
                float(printer_status_model.target_hotend_temperature))
            self._printer_output_model.updateBedTemperature(float(printer_status_model.bed_temperature))
            self._printer_output_model.updateTargetBedTemperature(float(printer_status_model.target_bed_temperature))
            if printer_status_model.state == MPSM2PrinterStatusModel.State.IDLE:
                self._printer_output_model.updateState('idle')
                self._print_job_model.updateState('not_started')
                self._print_job_model.updateProgress(0)
            elif printer_status_model.state == MPSM2PrinterStatusModel.State.PRINTING:  # printing includes paused print
                if self._printer_output_model.getPrinterState() == 'idle':
                    self._printer_output_model.updateState('printing')
                if self._print_job_model.getState() == 'not_started':
                    self._print_job_model.updateState('active')
                self._print_job_model.updateProgress(float(printer_status_model.progress))
            else:
                Logger.log('d', 'Unknown printer status')  # TODO: message
