"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
import os
from typing import List, Optional

from PyQt5.QtCore import pyqtProperty, pyqtSignal, QObject, pyqtSlot

from UM.FileHandler.FileHandler import FileHandler
from UM.Logger import Logger
from UM.i18n import i18nCatalog
from UM.Scene.SceneNode import SceneNode

# pylint:disable=import-error
from cura.CuraApplication import CuraApplication
from cura.PrinterOutput.Models.ExtruderConfigurationModel \
  import ExtruderConfigurationModel
from cura.PrinterOutput.Models.PrinterConfigurationModel \
  import PrinterConfigurationModel
from cura.PrinterOutput.Models.PrinterOutputModel import PrinterOutputModel
from cura.PrinterOutput.NetworkedPrinterOutputDevice \
  import NetworkedPrinterOutputDevice, AuthState
from cura.PrinterOutput.PrinterOutputDevice \
  import ConnectionType, ConnectionState

# pylint:disable=relative-beyond-top-level
from .MPSM2OutputController import MPSM2OutputController
from .Models.MPSM2PrinterOutputModel import MPSM2PrinterOutputModel
from .Models.MPSM2PrinterStatusModel import MPSM2PrinterStatusModel
from .Models.MPSM2PrintJobOutputModel import MPSM2PrintJobOutputModel
from .Network.ApiClient import ApiClient
from .GCodeWriteFileJob import GCodeWriteFileJob
from .Messages.PrintJobUploadProgressMessage \
  import PrintJobUploadProgressMessage
from .Messages.PrintJobUploadBlockedMessage \
  import PrintJobUploadBlockedMessage
from .Messages.PrintJobUploadSuccessMessage \
  import PrintJobUploadSuccessMessage
from .Messages.PrintJobUploadCancelMessage \
  import PrintJobUploadCancelMessage
from .Messages.PrintJobUploadIsPrintingMessage \
  import PrintJobUploadIsPrintingMessage
from .Parser.MPSM2PrinterStatusParser \
  import MPSM2PrinterStatusParser

I18N_CATALOG = i18nCatalog('cura')


def _build_printer_conf_model() -> PrinterConfigurationModel:
  """
  Returns:
    Printer's configuration model.
  """
  printer_configuration_model = PrinterConfigurationModel()
  extruder_conf_model = ExtruderConfigurationModel()
  extruder_conf_model.setPosition(0)
  printer_configuration_model.setExtruderConfigurations([extruder_conf_model])
  printer_configuration_model.setPrinterType('type')
  return printer_configuration_model


class MPSM2NetworkedPrinterOutputDevice(NetworkedPrinterOutputDevice):
  """Represents a networked OutputDevice for Monoprice Select Mini V2
  printers."""
  META_NETWORK_KEY = 'mpsm2_network_key'
  MPSM2_PROPERTIES = {
      b'name': b'Monoprice Select Mini V2',
      b'machine': b'Malyan M200',
      b'manual': b'true',
      b'printer_type': b'monoprice_select_mini_v2',
      b'firmware_version': b'Unknown',
  }

  printerStatusChanged = pyqtSignal()
  onPrinterUpload = pyqtSignal(bool)
  hasTargetHotendInProgressChanged = pyqtSignal()

  def __init__(self, device_id: str, address: str, parent=None) -> None:
    """Constructor

    Args:
      device_id: 'manual:<ip_address>'
      address: IP address, for example '192.168.0.70'
    """
    MPSM2NetworkedPrinterOutputDevice.MPSM2_PROPERTIES[b'address'] \
      = address.encode('utf-8')
    super().__init__(
        device_id=device_id,
        address=address,
        properties=MPSM2NetworkedPrinterOutputDevice.MPSM2_PROPERTIES,
        connection_type=ConnectionType.NetworkConnection,
        parent=parent)
    self._printer_output_controller = MPSM2OutputController(self)
    self._printer_raw_response = ''  # HTTP string response body
    self._is_busy = False
    self._has_target_hotend_in_progress = False

    # Set the display name from the properties.
    self.setName(self.getProperty('name'))

    # Set the display name of the printer type.
    definitions = CuraApplication.getInstance().getContainerRegistry() \
      .findContainers(id=self.printerType)
    self._printer_type_name = definitions[0].getName() if definitions else ''
    self._job_upload_message = PrintJobUploadProgressMessage(
        self._on_print_upload_cancelled)
    self._api_client = ApiClient(self.address,
                                 on_error=lambda error: Logger.log('e',
                                                                   str(error)))

    self._print_job_model = MPSM2PrintJobOutputModel(
        self._printer_output_controller)
    self._printer_output_model = \
      self._build_printer_output_model()  # type: MPSM2PrinterOutputModel

    self.setAuthenticationState(AuthState.Authenticated)
    self._load_monitor_tab()
    self._set_ui_elements()

  @pyqtProperty(QObject, notify=printerStatusChanged)
  def printer(self) -> PrinterOutputModel:
    """Produces main object for rendering the Printer Monitor tab."""
    if self._printer_raw_response.upper() != 'OK':
      self._on_printer_status_changed(self._printer_raw_response)
    return self._printer_output_model

  # pylint:disable=invalid-name
  @pyqtProperty(bool, notify=onPrinterUpload)
  def isUploading(self) -> bool:
    """
    Returns:
       true if user is uploading a model to the printer.
    """
    return self._is_busy

  @pyqtProperty(bool, notify=hasTargetHotendInProgressChanged)
  def has_target_hotend_in_progress(self) -> bool:
    """
    Returns:
       true if there is a request to update hot-end temperature in progress.
    """
    return self._has_target_hotend_in_progress

  @pyqtSlot(str, name='setTargetHotendTemperature')
  def set_target_hotend_temperature(
      self,
      target_hotend_temperature_celsius: str) -> None:
    Logger.log('d', 'Setting target hotend temperature to %sºC',
               target_hotend_temperature_celsius)
    try:
      self._has_target_hotend_in_progress = True
      self.hasTargetHotendInProgressChanged.emit()
      self._api_client.set_target_hotend_temperature(
          int(target_hotend_temperature_celsius),
          self._on_target_hotend_temperature_finished)
    except ValueError:
      Logger.log('e', 'Invalid target hotend temperature %s',
                 target_hotend_temperature_celsius)

  @pyqtSlot(name='startPrint')
  def start_print(self) -> None:
    """Prints the cached model in printer."""
    Logger.log('d', 'Printing cache.gc.')
    self._api_client.start_print(self._on_print_started)

  @pyqtSlot(name='pauseOrResumePrint')
  def pause_or_resume_print(self) -> None:
    """Pauses or resumes the print job."""
    if self._print_job_model.get_state() == 'paused':
      Logger.log('d', 'Resuming print.')
      self._api_client.resume_print(self._on_print_resumed)
    else:
      Logger.log('d', 'Pausing print.')
      self._api_client.pause_print(self._on_print_paused)

  @pyqtSlot(name='cancelPrint')
  def cancel_print(self) -> None:
    """Cancels the print job."""
    Logger.log('d', 'Cancelling print.')
    self._api_client.cancel_print(self._on_print_cancelled)

  # Override
  def connect(self) -> None:
    """Connects to the printer."""
    Logger.log('d', 'Connecting.')
    super().connect()
    self._update()

  # Override
  def close(self) -> None:
    """Closes the connection to the printer."""
    Logger.log('d', 'Closing.')
    super().close()
    self.setConnectionState(ConnectionState.Closed)
    if self.key in CuraApplication.getInstance().getOutputDeviceManager() \
        .getOutputDeviceIds():
      CuraApplication.getInstance().getOutputDeviceManager().removeOutputDevice(
          self.key)

  # Override
  # pylint:disable=invalid-name
  # pylint:disable=unused-argument
  def requestWrite(self, nodes: List[SceneNode],
                   file_name: Optional[str] = None,
                   limit_mimetypes: bool = False,
                   file_handler: Optional[FileHandler] = None,
                   filter_by_machine: bool = False, **kwargs) -> None:
    """Initiates the job upload to printer.
    Called when user clicks on button 'Print over the network'.

    Args:
      nodes: A collection of scene nodes that should be written to the device.
      file_name: unused.
      limit_mimetypes: unused.
      file_handler: The filehandler to use to write the file with.
      filter_by_machine: unused.
    """
    Logger.log('d', 'Write to Output Device was requested.')
    if self._job_upload_message.visible:
      PrintJobUploadBlockedMessage().show()
      return
    if self._printer_output_model.get_printer_state() == 'printing':
      PrintJobUploadIsPrintingMessage().show()
      return

    self.writeStarted.emit(self)
    job = GCodeWriteFileJob(file_handler=file_handler, nodes=nodes)
    job.finished.connect(self._on_print_job_created)
    job.start()

  def update_printer_status(self, raw_response: str) -> None:
    """Updates printer status.

    Args:
      raw_response: HTTP body response containing the printer status.
    """
    self._printer_raw_response = raw_response

  def is_busy(self) -> bool:
    """
    Returns:
      true if the printer is uploading a job.
    """
    return self._is_busy

  def _on_print_job_created(self, job: GCodeWriteFileJob) -> None:
    """Called when a print job starts to upload.

    Args:
      job: job that is being uploaded.
    """
    if not job:
      Logger.log('e', 'No active exported job to upload!')
      return
    self.onPrinterUpload.emit(True)
    self._is_busy = True
    self._job_upload_message.show()
    self._api_client.upload_print(job.getFileName(), job.get_gcode_output(),
                                  self._on_print_upload_completed,
                                  self._on_print_job_upload_progress)

  def _on_print_upload_cancelled(self) -> None:
    """Called when the user cancels the print upload."""
    self._is_busy = False
    self._job_upload_message.hide()
    self._api_client.cancel_upload_print()
    self._api_client.cancel_print()  # force cancel
    PrintJobUploadCancelMessage().show()
    self.writeFinished.emit()
    self.onPrinterUpload.emit(False)

  def _on_print_upload_completed(self, raw_response: str) -> None:
    """Called when the print job upload is completed.

    Args:
      raw_response: HTTP body response from upload request.
    """
    self._printer_raw_response = raw_response
    if raw_response.upper() == 'OK':
      self._is_busy = False
      self._job_upload_message.hide()
      PrintJobUploadSuccessMessage().show()
      self._api_client.start_print()  # force start
      self.writeFinished.emit()
      self.onPrinterUpload.emit(False)
    else:
      Logger.log('e', 'Could not upload print.')

  def _on_print_job_upload_progress(self, bytes_sent: int,
                                    bytes_total: int) -> None:
    """Called periodically by Cura to update the upload progress.

    Args:
      bytes_sent: number of bytes already sent to the printer.
      bytes_total: total bytes to be sent.
    """
    percentage = (bytes_sent / bytes_total) if bytes_total else 0
    self._job_upload_message.setProgress(percentage * 100)
    self.writeProgress.emit()

  def _on_print_started(self, raw_response: str) -> None:
    """Called when the user starts the print job.

    Args:
      raw_response: HTTP response to the start request.
    """
    self._on_print_resumed(raw_response)

  def _on_print_resumed(self, raw_response: str) -> None:
    """Called when the user resumes the print job.

    Args:
      raw_response: HTTP response to the resume request.
    """
    self._printer_raw_response = raw_response
    if raw_response.upper() == 'OK':
      self._printer_output_model.updateState('printing')
      self._print_job_model.updateState('active')
      self.printerStatusChanged.emit()
    else:
      Logger.log('e', 'Could not resume print')  # TODO message

  def _on_print_paused(self, raw_response: str) -> None:
    """Called when the user pauses the print job.

    Args:
      raw_response: HTTP response to the pause request.
    """
    self._printer_raw_response = raw_response
    if raw_response.upper() == 'OK':
      self._printer_output_model.updateState('paused')
      self._print_job_model.updateState('paused')
      self.printerStatusChanged.emit()
    else:
      Logger.log('e', 'Could not pause print')  # TODO: message

  def _on_print_cancelled(self, raw_response: str) -> None:
    """Called when the user cancels the print job.

    Args:
      raw_response: HTTP response to the cancel request.
    """
    self._printer_raw_response = raw_response
    if raw_response.upper() == 'OK':
      self._printer_output_model.updateState('idle')
      self._print_job_model.updateState('not_started')
      self._print_job_model.update_progress(0)
      self.printerStatusChanged.emit()
    else:
      Logger.log('e', 'Could not cancel print')  # TODO: message

  def _on_target_hotend_temperature_finished(self, raw_response: str) -> None:
    """Called when a request to set target hotend temperature completed.

    Args:
      raw_response: HTTP response to the target hotend temperature request.
    """
    self._printer_raw_response = raw_response
    if raw_response.upper() == 'OK':
      self._has_target_hotend_in_progress = False
      self.hasTargetHotendInProgressChanged.emit()
    else:
      # TODO: UI message
      Logger.log('e', 'Could not set target hotend temperature.')

  def _set_ui_elements(self) -> None:
    """Sets Cura UI elements corresponding to this device."""
    self.setPriority(
        3)  # Make sure the output device gets selected above local file output
    self.setShortDescription(
        I18N_CATALOG.i18nc('@action:button Preceded by "Ready to".',
                           'Print over network'))
    self.setDescription(
        I18N_CATALOG.i18nc('@properties:tooltip', 'Print over network'))
    self.setConnectionText(
        I18N_CATALOG.i18nc('@info:status', 'Connected over the network'))

  def _load_monitor_tab(self) -> None:
    """Loads the QML resources to display the monitor tab in Cura."""
    plugin_registry = CuraApplication.getInstance().getPluginRegistry()
    if not plugin_registry:
      Logger.log('e', 'Could not get plugin registry.')
      return
    plugin_path = plugin_registry.getPluginPath('MPSM2NetworkPrinting')
    if not plugin_path:
      Logger.log('e', 'Could not get plugin path.')
      return
    self._monitor_view_qml_path = os.path.join(plugin_path, 'resources', 'qml',
                                               'MonitorStage.qml')

  def _build_printer_output_model(self) -> MPSM2PrinterOutputModel:
    """
    Returns:
      Printer Output Model for this device.
    """
    printer_output_model = MPSM2PrinterOutputModel(
        self._printer_output_controller)
    printer_output_model.updateKey(self._address)
    printer_output_model.updateName(self.address)
    printer_output_model.updateState('idle')
    printer_output_model.setAvailableConfigurations(
        [_build_printer_conf_model()])
    printer_output_model.updateType('Monoprice Select Mini')
    printer_output_model.updateActivePrintJob(self._print_job_model)
    return printer_output_model

  def _on_printer_status_changed(self, raw_response: str) -> None:
    """Called when the printer status response is received.

    Args:
      raw_response: HTTP body response to the printer status request.
    """
    printer_status_model = MPSM2PrinterStatusParser.parse(raw_response)
    if printer_status_model:
      self._printer_output_model.extruders[0].updateHotendTemperature(
          float(printer_status_model.hotend_temperature))
      self._printer_output_model.extruders[0].updateTargetHotendTemperature(
          float(printer_status_model.target_hotend_temperature))
      self._printer_output_model.updateBedTemperature(
          float(printer_status_model.bed_temperature))
      self._printer_output_model.updateTargetBedTemperature(
          float(printer_status_model.target_bed_temperature))
      if printer_status_model.state == MPSM2PrinterStatusModel.State.IDLE:
        self._printer_output_model.updateState('idle')
        self._print_job_model.updateState('not_started')
        self._print_job_model.update_progress(0)
      elif printer_status_model.state == MPSM2PrinterStatusModel.State.PRINTING:
        # PRINTING includes paused print
        if self._printer_output_model.get_printer_state() == 'idle':
          self._printer_output_model.updateState('printing')
        if self._print_job_model.get_state() == 'not_started':
          self._print_job_model.updateState('active')
        self._print_job_model.update_progress(
            float(printer_status_model.progress))
      else:
        Logger.log('e', 'Unknown printer status')  # TODO: message
