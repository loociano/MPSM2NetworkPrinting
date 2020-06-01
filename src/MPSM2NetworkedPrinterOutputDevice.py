"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
import os
from typing import List, Optional

from PyQt5.QtCore import pyqtProperty, pyqtSignal, QObject, pyqtSlot

from UM.FileHandler.FileHandler import FileHandler
from UM.Logger import Logger
from UM.Scene.SceneNode import SceneNode
from UM.i18n import i18nCatalog

# pylint:disable=import-error
from cura.CuraApplication import CuraApplication
from cura.PrinterOutput.Models.ExtruderConfigurationModel import \
  ExtruderConfigurationModel
from cura.PrinterOutput.Models.PrinterConfigurationModel import \
  PrinterConfigurationModel
from cura.PrinterOutput.NetworkedPrinterOutputDevice \
  import NetworkedPrinterOutputDevice, AuthState
from cura.PrinterOutput.PrinterOutputDevice \
  import ConnectionType, ConnectionState

# pylint:disable=relative-beyond-top-level
from .GCodeWriteFileJob import GCodeWriteFileJob
from .MPSM2OutputController import MPSM2OutputController
from .messages.NetworkErrorMessage import NetworkErrorMessage
from .messages.PrintJobCancelErrorMessage import PrintJobCancelErrorMessage
from .messages.PrintJobPauseErrorMessage import PrintJobPauseErrorMessage
from .messages.PrintJobStartErrorMessage import PrintJobStartErrorMessage
from .messages.PrintJobUploadBlockedMessage \
  import PrintJobUploadBlockedMessage
from .messages.PrintJobUploadCancelMessage \
  import PrintJobUploadCancelMessage
from .messages.PrintJobUploadIsPrintingMessage \
  import PrintJobUploadIsPrintingMessage
from .messages.PrintJobUploadProgressMessage \
  import PrintJobUploadProgressMessage
from .messages.PrintJobUploadSuccessMessage \
  import PrintJobUploadSuccessMessage
from .messages.SetTargetTemperatureErrorMessage import SetTargetTemperatureErrorMessage
from .models.MPSM2PrintJobOutputModel import MPSM2PrintJobOutputModel
from .models.MPSM2PrinterOutputModel import MPSM2PrinterOutputModel
from .models.MPSM2PrinterStatusModel import MPSM2PrinterStatusModel
from .network.ApiClient import ApiClient
from .parser.MPSM2PrinterStatusParser \
  import MPSM2PrinterStatusParser

I18N_CATALOG = i18nCatalog('cura')


class MPSM2NetworkedPrinterOutputDevice(NetworkedPrinterOutputDevice):
  """Represents a networked OutputDevice for Monoprice Select Mini V2
  printers."""
  MAX_TARGET_HOTEND_TEMPERATURE = 260  # celsius
  MAX_TARGET_BED_TEMPERATURE = 85  # celsius

  printerStatusChanged = pyqtSignal()
  onPrinterUpload = pyqtSignal(bool)
  startPrintRequestChanged = pyqtSignal()
  pausePrintRequestChanged = pyqtSignal()
  cancelPrintRequestChanged = pyqtSignal()
  hasTargetHotendInProgressChanged = pyqtSignal()
  hasTargetBedInProgressChanged = pyqtSignal()

  def __init__(self, device_id: str, address: str, parent=None) -> None:
    """Constructor.

    Args:
      device_id: 'manual:<ip_address>'
      address: IP address, for example '192.168.0.70'
    """
    device_name = 'MPSM V2 {}'.format(address)
    mpsm2_properties = {
        b'name': device_name.encode('utf-8'),
        b'machine': b'Malyan M200',
        b'manual': b'true',
        b'printer_type': b'monoprice_select_mini_v2',
        b'firmware_version': b'Unknown',
        b'address': address.encode('utf-8'),
    }
    super().__init__(
        device_id=device_id,
        address=address,
        properties=mpsm2_properties,
        connection_type=ConnectionType.NetworkConnection,
        parent=parent)
    self._printer_output_controller = MPSM2OutputController(self)
    self._is_busy = False
    self._requested_start_print = False
    self._requested_pause_print = False
    self._requested_cancel_print = False
    self._requested_hotend_temperature = None  # int
    self._requested_bed_temperature = None  # int
    self.setName(device_name)

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
    self._api_client.increase_upload_speed(
        self._on_increased_upload_speed,
        self._on_increased_upload_speed_error)

  @pyqtProperty(QObject, notify=printerStatusChanged)
  def printer(self) -> MPSM2PrinterOutputModel:
    """Produces main object for rendering the Printer Monitor tab."""
    return self._printer_output_model

  @pyqtProperty(int, constant=True)
  def max_hotend_temperature(self) -> int:
    """
    Returns:
      Maximum target hotend temperature for UI message.
    """
    return self.MAX_TARGET_HOTEND_TEMPERATURE

  @pyqtProperty(int, constant=True)
  def max_bed_temperature(self) -> int:
    """
    Returns:
       maximum target bed temperature for UI message.
    """
    return self.MAX_TARGET_BED_TEMPERATURE

  # pylint:disable=invalid-name
  @pyqtProperty(bool, notify=onPrinterUpload)
  def isUploading(self) -> bool:
    """
    Returns:
       true if user is uploading a model to the printer.
    """
    return self._is_busy

  @pyqtProperty(bool, notify=startPrintRequestChanged)
  def has_start_print_request_in_progress(self) -> bool:
    """
    Returns:
       true while printer is not printing.
    """
    return self._requested_start_print

  @pyqtProperty(bool, notify=pausePrintRequestChanged)
  def has_pause_print_request_in_progress(self) -> bool:
    """
    Returns:
       true while the printer continues printing.
    """
    return self._requested_pause_print

  @pyqtProperty(bool, notify=cancelPrintRequestChanged)
  def has_cancel_print_request_in_progress(self) -> bool:
    """
    Returns:
       true while the printer continues printing.
    """
    return self._requested_cancel_print

  @pyqtProperty(bool, notify=hasTargetHotendInProgressChanged)
  def has_target_hotend_in_progress(self) -> bool:
    """
    Returns:
       true if there is a request to update hot-end temperature in progress.
    """
    return self._requested_hotend_temperature is not None

  @pyqtProperty(bool, notify=hasTargetBedInProgressChanged)
  def has_target_bed_in_progress(self) -> bool:
    """
    Returns:
       true if there is a request to update bed temperature in progress.
    """
    return self._requested_bed_temperature is not None

  @pyqtSlot(str, name='isValidHotendTemperature', result=bool)
  def is_valid_hotend_temperature(self, input_temperature: str) -> bool:
    """
    Args:
      input_temperature: user-entered target hotend temperature.
    Returns:
       true if temperature within range.
    """
    if not input_temperature.isdigit():
      return False
    if int(input_temperature) < 0 \
        or int(input_temperature) > self.MAX_TARGET_HOTEND_TEMPERATURE:
      return False
    return True

  @pyqtSlot(str, name='isValidBedTemperature', result=bool)
  def is_valid_bed_temperature(self, input_temperature: str) -> bool:
    """
    Args:
      input_temperature: user-entered target bed temperature.
    Returns:
       true if temperature within range.
    """
    if not input_temperature.isdigit():
      return False
    if int(input_temperature) < 0 \
        or int(input_temperature) > self.MAX_TARGET_BED_TEMPERATURE:
      return False
    return True

  @pyqtSlot(str, name='setTargetHotendTemperature')
  def set_target_hotend_temperature(self, celsius: str) -> None:
    """Called when the user requests a target hotend temperature.

    Args:
      celsius: requested target hotend temperature. Can be invalid.
    """
    Logger.log('d', 'Setting target hotend temperature to %sºC.', celsius)
    try:
      self._api_client.set_target_hotend_temperature(
          int(celsius),
          self._on_target_hotend_temperature_finished,
          self._on_target_hotend_temperature_error)
      self._requested_hotend_temperature = int(celsius)
      self.hasTargetHotendInProgressChanged.emit()
    except ValueError:
      Logger.log('e', 'Invalid target hotend temperature %s.', celsius)

  @pyqtSlot(str, name='setTargetBedTemperature')
  def set_target_bed_temperature(self, celsius: str) -> None:
    """Called when the user requests a target bed temperature.

    Args:
      celsius: requested target bed temperature. Can be invalid.
    """
    Logger.log('d', 'Setting target bed temperature to %sºC.', celsius)
    try:
      self._api_client.set_target_bed_temperature(
          int(celsius),
          self._on_target_bed_temperature_finished,
          self._on_target_bed_temperature_error)
      self._requested_bed_temperature = int(celsius)
      self.hasTargetBedInProgressChanged.emit()
    except ValueError:
      Logger.log('e', 'Invalid target bed temperature %s.', celsius)

  @pyqtSlot(name='startPrint')
  def start_print(self) -> None:
    """Prints the cached model in printer."""
    Logger.log('d', 'Printing cache.gc.')
    self._api_client.start_print(self._on_print_started,
                                 self._on_print_started_error)
    self._requested_start_print = True
    self.startPrintRequestChanged.emit()

  @pyqtSlot(name='resumePrint')
  def resume_print(self) -> None:
    """Resumes the print job."""
    Logger.log('d', 'Resuming print.')
    self._api_client.resume_print(self._on_print_resumed)
    self._requested_start_print = True
    self.startPrintRequestChanged.emit()

  @pyqtSlot(name='pausePrint')
  def pause_print(self) -> None:
    """Pauses the print job."""
    Logger.log('d', 'Pausing print.')
    self._api_client.pause_print(self._on_print_paused,
                                 self._on_print_paused_error)
    self._requested_pause_print = True
    self.pausePrintRequestChanged.emit()

  @pyqtSlot(name='cancelPrint')
  def cancel_print(self) -> None:
    """Cancels the print job."""
    Logger.log('d', 'Cancelling print.')
    self._api_client.cancel_print(self._on_print_cancelled,
                                  self._on_print_cancelled_error)
    self._requested_cancel_print = True
    self.cancelPrintRequestChanged.emit()

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

  def update_printer_status(self, response: str) -> None:
    """Updates printer status.

    Args:
      response: HTTP body response containing the printer status.
    """
    self._on_printer_status_changed(response)
    self.printerStatusChanged.emit()

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

  def _on_print_upload_completed(self, response: str) -> None:
    """Called when the print job upload is completed.

    Args:
      response: HTTP body response from upload request.
    """
    if response.upper() == 'OK':
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
    self._job_upload_message.update(bytes_sent, bytes_total)
    self.writeProgress.emit()

  def _on_print_started(self, response: str) -> None:
    """Called when the user starts the print job.

    Args:
      response: HTTP response to the start request.
    """
    self._on_print_resumed(response)

  def _on_print_resumed(self, response: str) -> None:
    """Called when the user resumes the print job.

    Args:
      response: HTTP response to the resume request.
    """
    if response.upper() != 'OK':
      self._on_print_started_error()

  def _on_print_started_error(self) -> None:
    """Called if there was an error to communicate the printer to start printing."""
    self._requested_start_print = False
    PrintJobStartErrorMessage().show()
    self.startPrintRequestChanged.emit()

  def _on_print_paused(self, response: str) -> None:
    """Called when the user pauses the print job.

    Args:
      response: HTTP response to the pause request.
    """
    if response.upper() != 'OK':
      self._on_print_paused_error()

  def _on_print_paused_error(self) -> None:
    """Called if there was an error to communicate the printer to pause."""
    self._requested_pause_print = False
    PrintJobPauseErrorMessage().show()
    self.pausePrintRequestChanged.emit()

  def _on_print_cancelled(self, response: str) -> None:
    """Called when the user cancels the print job.

    Args:
      response: HTTP response to the cancel request.
    """
    if response.upper() != 'OK':
      self._on_print_cancelled_error()

  def _on_print_cancelled_error(self) -> None:
    """Called if there was an error to communicate the printer to cancel."""
    self._requested_cancel_print = False
    PrintJobCancelErrorMessage().show()
    self.cancelPrintRequestChanged.emit()

  def _on_target_hotend_temperature_finished(self, response: str) -> None:
    """Called when a request to set target hotend temperature completed.

    Args:
      response: HTTP response to the target temperature request.
    """
    if response.upper() != 'OK':
      self._on_target_hotend_temperature_error()

  def _on_target_hotend_temperature_error(self) -> None:
    """Called if there was an error setting target hotend temperature."""
    self._requested_hotend_temperature = False
    SetTargetTemperatureErrorMessage().show()
    self.hasTargetHotendInProgressChanged.emit()

  def _on_target_bed_temperature_finished(self, response: str) -> None:
    """Called when a request to set target bed temperature completed.

    Args:
      response: HTTP response to the target temperature request.
    """
    if response.upper() != 'OK':
      self._on_target_bed_temperature_error()

  def _on_target_bed_temperature_error(self) -> None:
    """Called if there was an error setting target bed temperature."""
    self._requested_bed_temperature = False
    SetTargetTemperatureErrorMessage().show()
    self.hasTargetBedInProgressChanged.emit()

  def _on_increased_upload_speed(self, response: str) -> None:
    """Called when a request to increase upload speed completed.

    Args:
      response: HTTP response to the gcode command request.
    """
    if response.upper() != 'OK':
      self._on_increased_upload_speed_error()

  def _on_increased_upload_speed_error(self) -> None:
    NetworkErrorMessage().show()

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

  @staticmethod
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
        [MPSM2NetworkedPrinterOutputDevice._build_printer_conf_model()])
    printer_output_model.updateType('Monoprice Select Mini')
    printer_output_model.updateActivePrintJob(self._print_job_model)
    return printer_output_model

  def _on_printer_status_changed(self, response: str) -> None:
    """Called when the printer status response is received.

    Args:
      response: HTTP body response to the printer status request.
    """
    printer_status_model = MPSM2PrinterStatusParser.parse(response)
    if printer_status_model:
      self._update_printer_output_model(printer_status_model)

  def _update_printer_output_model(
      self,
      printer_status_model: MPSM2PrinterStatusModel) -> None:
    """Updates printer and print job output models.

    Args:
      printer_status_model: parsed model from printer's status response.
    """
    self._update_model_temperatures(printer_status_model)

    if printer_status_model.state == MPSM2PrinterStatusModel.State.IDLE:
      self._printer_output_model.updateState('idle')
      self._print_job_model.updateState('not_started')
      self._print_job_model.update_progress(0)

      if self._requested_cancel_print:
        self._requested_cancel_print = False  # Fulfilled
        self.cancelPrintRequestChanged.emit()

    elif printer_status_model.state == MPSM2PrinterStatusModel.State.PRINTING:
      self._printer_output_model.updateState('printing')
      self._print_job_model.updateState('active')
      self._print_job_model.update_progress(
          float(printer_status_model.progress))

      if self._requested_start_print:
        self._requested_start_print = False  # Fulfilled.
        self.startPrintRequestChanged.emit()

      # Printer does not acknowledge that the printing is paused.
      # PRINTING state includes paused.
      if self._requested_pause_print:
        self._requested_pause_print = False  # Fulfilled.
        self.pausePrintRequestChanged.emit()

    else:
      Logger.log('e', 'Unknown printer status.')
      NetworkErrorMessage().show()

  def _update_model_temperatures(
      self,
      printer_status_model: MPSM2PrinterStatusModel) -> None:
    """Updates temperatures in the printer's output model.

    Args:
      printer_status_model: parsed model from printer's status response.
    """
    self._printer_output_model.extruders[0].updateHotendTemperature(
        float(printer_status_model.hotend_temperature))
    self._printer_output_model.extruders[0].updateTargetHotendTemperature(
        float(printer_status_model.target_hotend_temperature))
    self._printer_output_model.updateBedTemperature(
        float(printer_status_model.bed_temperature))
    self._printer_output_model.updateTargetBedTemperature(
        float(printer_status_model.target_bed_temperature))

    if self._requested_hotend_temperature \
        == printer_status_model.target_hotend_temperature:
      self._requested_hotend_temperature = None
      self.hasTargetHotendInProgressChanged.emit()

    if self._requested_bed_temperature \
        == printer_status_model.target_bed_temperature:
      self._requested_bed_temperature = None
      self.hasTargetBedInProgressChanged.emit()
