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
from cura.PrinterOutput.Models.ExtruderConfigurationModel import ExtruderConfigurationModel
from cura.PrinterOutput.Models.PrinterConfigurationModel import PrinterConfigurationModel
from cura.PrinterOutput.Models.PrinterOutputModel import PrinterOutputModel
from cura.PrinterOutput.NetworkedPrinterOutputDevice import NetworkedPrinterOutputDevice, AuthState
from cura.PrinterOutput.PrinterOutputDevice import ConnectionType, ConnectionState
# pylint:disable=relative-beyond-top-level
from .GCodeWriteFileJob import GCodeWriteFileJob
from .MPSM2OutputController import MPSM2OutputController
from .messages.NetworkErrorMessage import NetworkErrorMessage
from .messages.PrintJobCancelErrorMessage import PrintJobCancelErrorMessage
from .messages.PrintJobPauseErrorMessage import PrintJobPauseErrorMessage
from .messages.PrintJobStartErrorMessage import PrintJobStartErrorMessage
from .messages.PrintJobUploadBlockedMessage import PrintJobUploadBlockedMessage
from .messages.PrintJobUploadCancelMessage import PrintJobUploadCancelMessage
from .messages.PrintJobUploadErrorMessage import PrintJobUploadErrorMessage
from .messages.PrintJobUploadIsPrintingMessage import PrintJobUploadIsPrintingMessage
from .messages.PrintJobUploadProgressMessage import PrintJobUploadProgressMessage
from .messages.PrintJobUploadSuccessMessage import PrintJobUploadSuccessMessage
from .messages.SetTargetTemperatureErrorMessage import SetTargetTemperatureErrorMessage
from .models.MPSM2PrintJobOutputModel import MPSM2PrintJobOutputModel
from .models.MPSM2PrinterStatusModel import MPSM2PrinterStatusModel
from .network.ApiClient import ApiClient
from .parsers.GcodePreheatSettingsParser import GcodePreheatSettingsParser
from .parsers.MPSM2PrinterStatusParser import MPSM2PrinterStatusParser

I18N_CATALOG = i18nCatalog('cura')
# Monoprice Select Mini V2 printer has a single extruder.
_NUM_EXTRUDERS = 1


class MPSM2NetworkedPrinterOutputDevice(NetworkedPrinterOutputDevice):
  """Networked OutputDevice for Monoprice Select Mini V2 printers."""
  MAX_TARGET_HOTEND_TEMPERATURE = 260  # celsius
  MAX_TARGET_BED_TEMPERATURE = 85  # celsius
  NUM_DATA_POINTS = 30

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
    device_name = f'MPSM V2 {address}'
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
    self._is_uploading = False
    self._requested_start_print = False
    self._requested_pause_print = False
    self._requested_cancel_print = False
    self._requested_hotend_temperature = None  # int
    self._requested_bed_temperature = None  # int
    self._historical_hotend_temps = []  # List[int]
    self._historical_bed_temps = []  # List[int]
    self.setName(device_name)
    self._preheat_bed_temperature = None
    self._preheat_hotend_temperature = None

    self._job_upload_message = PrintJobUploadProgressMessage(
        self._on_print_upload_cancelled)
    self._api_client = ApiClient(self.address)

    self._print_job_model = MPSM2PrintJobOutputModel(
        self._printer_output_controller)
    self._printer_output_model = self._build_printer_output_model()

    self.setAuthenticationState(AuthState.Authenticated)
    self._load_monitor_tab()
    self._set_ui_elements()
    self._api_client.increase_upload_speed(
        self._on_increased_upload_speed,
        self._on_increased_upload_speed_error)

  @pyqtProperty(QObject, notify=printerStatusChanged)
  def printer(self) -> PrinterOutputModel:
    """Produces main object for rendering the Printer Monitor tab."""
    return self._printer_output_model

  @pyqtProperty(list, notify=printerStatusChanged)
  def historical_hotend_temperatures(self) -> list:
    return self._historical_hotend_temps

  @pyqtProperty(list, notify=printerStatusChanged)
  def historical_bed_temperatures(self) -> list:
    return self._historical_bed_temps

  @pyqtProperty(int, constant=True)
  def max_hotend_temperature(self) -> int:
    """Returns maximum target hotend temperature for UI message.
    """
    return self.MAX_TARGET_HOTEND_TEMPERATURE

  @pyqtProperty(int, constant=True)
  def max_bed_temperature(self) -> int:
    """Returns maximum target bed temperature for UI message.
    """
    return self.MAX_TARGET_BED_TEMPERATURE

  # pylint:disable=invalid-name
  @pyqtProperty(bool, notify=onPrinterUpload)
  def isUploading(self) -> bool:
    """Returns True if user is uploading a model to the printer.
    """
    return self._is_uploading

  @pyqtProperty(bool, notify=startPrintRequestChanged)
  def has_start_print_request_in_progress(self) -> bool:
    """Returns True while printer is not printing.
    """
    return self._requested_start_print

  @pyqtProperty(bool, notify=pausePrintRequestChanged)
  def has_pause_print_request_in_progress(self) -> bool:
    """Returns True while the printer continues printing.
    """
    return self._requested_pause_print

  @pyqtProperty(bool, notify=cancelPrintRequestChanged)
  def has_cancel_print_request_in_progress(self) -> bool:
    """Returns True while the printer continues printing.
    """
    return self._requested_cancel_print

  @pyqtProperty(bool, notify=hasTargetHotendInProgressChanged)
  def has_target_hotend_in_progress(self) -> bool:
    """Returns True if there is a request to update hot-end temperature in
    progress.
    """
    return self._requested_hotend_temperature is not None

  @pyqtProperty(bool, notify=hasTargetBedInProgressChanged)
  def has_target_bed_in_progress(self) -> bool:
    """Returns True if there is a request to update bed temperature in progress.
    """
    return self._requested_bed_temperature is not None

  @pyqtSlot(str, name='isValidHotendTemperature', result=bool)
  def is_valid_hotend_temperature(self, input_temperature: str) -> bool:
    """Checks if the input hotend temperature is valid.

    Args:
      input_temperature: User-entered target hotend temperature.

    Returns:
       True if temperature within range.
    """
    if not input_temperature.isdigit():
      return False
    return 0 <= int(input_temperature) <= self.MAX_TARGET_HOTEND_TEMPERATURE

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
    return 0 <= int(input_temperature) <= self.MAX_TARGET_BED_TEMPERATURE

  @pyqtSlot(str, name='setTargetHotendTemperature')
  def set_target_hotend_temperature(self, celsius: str) -> None:
    """Called when the user requests a target hotend temperature.

    Args:
      celsius: Requested target hotend temperature. Can be invalid.
    """
    Logger.log('d', 'Setting target hotend temperature to %sºC.', celsius)
    try:
      self._api_client.set_target_hotend_temperature(
          temperature=int(celsius),
          on_finished=self._on_target_hotend_temperature_finished,
          on_error=self._on_target_hotend_temperature_error)
      self._requested_hotend_temperature = int(celsius)
      self.hasTargetHotendInProgressChanged.emit()
    except ValueError:
      Logger.log('e', 'Invalid target hotend temperature %s.', celsius)

  @pyqtSlot(str, name='setTargetBedTemperature')
  def set_target_bed_temperature(self, celsius: str) -> None:
    """Called when the user requests a target bed temperature.

    Args:
      celsius: Requested target bed temperature. Can be invalid.
    """
    Logger.log('d', 'Setting target bed temperature to %sºC.', celsius)
    try:
      self._api_client.set_target_bed_temperature(
          temperature=int(celsius),
          on_finished=self._on_target_bed_temperature_finished,
          on_error=self._on_target_bed_temperature_error)
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
    device_manager = CuraApplication.getInstance().getOutputDeviceManager()
    if self.key in device_manager.getOutputDeviceIds():
      device_manager.removeOutputDevice(self.key)

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
      limit_mimetypes: Limits MIME types. Unused.
      file_handler: The file handler to use to write the file with.
      filter_by_machine: Whether to filter by machine. Unused.
    """
    Logger.log('d', 'Write to Output Device was requested.')
    if self._job_upload_message.visible:
      PrintJobUploadBlockedMessage().show()
      return
    if self._printer_output_model.state == 'printing':
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

  def is_uploading(self) -> bool:
    """Returns True if the printer is uploading a job."""
    return self._is_uploading

  def _on_print_job_created(self, job: GCodeWriteFileJob) -> None:
    """Called when a print job starts to upload.

    Args:
      job: Job that is being uploaded.
    """
    if not job:
      Logger.log('e', 'No active exported job to upload!')
      return
    self.onPrinterUpload.emit(True)
    self._is_uploading = True
    self._job_upload_message.show()
    gcode = job.get_gcode_output()
    self._preheat_bed_temperature, self._preheat_hotend_temperature = (
        GcodePreheatSettingsParser.parse(gcode))
    self._api_client.upload_print(job.getFileName(), gcode,
                                  self._on_print_job_upload_completed,
                                  self._on_print_job_upload_progress,
                                  self._on_print_job_upload_error)

  def _on_print_upload_cancelled(self) -> None:
    """Called when the user cancels the print upload."""
    self._is_uploading = False
    self._job_upload_message.hide()
    self._api_client.cancel_upload_print()
    self._api_client.cancel_print()  # Force cancel.
    PrintJobUploadCancelMessage().show()
    self.writeFinished.emit()
    self.onPrinterUpload.emit(False)

  def _on_print_job_upload_error(self) -> None:
    """Called if there was an error uploading the model."""
    if self._is_uploading:
      self._is_uploading = False
      self._job_upload_message.hide()
      self._api_client.cancel_upload_print()
      self._api_client.cancel_print()  # Force cancel.
      PrintJobUploadErrorMessage().show()
      self.writeError.emit()
      self.onPrinterUpload.emit(False)

  def _on_print_job_upload_completed(self, response: str) -> None:
    """Called when the print job upload is completed.

    Args:
      response: HTTP body response from upload request.
    """
    if response.upper() == 'OK':
      self._is_uploading = False
      self._job_upload_message.hide()
      PrintJobUploadSuccessMessage().show()
      if self._preheat_bed_temperature is not None:
        # Force bed preheating
        self._api_client.set_target_bed_temperature(
            temperature=self._preheat_bed_temperature,
            on_finished=self._on_target_bed_temperature_finished,
            on_error=self._on_target_bed_temperature_error)
      if self._preheat_hotend_temperature is not None:
        # Force hotend preheating
        self._api_client.set_target_hotend_temperature(
            temperature=self._preheat_hotend_temperature,
            on_finished=self._on_target_hotend_temperature_finished,
            on_error=self._on_target_hotend_temperature_error)
        # Force start. Sometimes the printer does not start automatically.
        self._api_client.start_print()
      self.writeFinished.emit()
      self.onPrinterUpload.emit(False)
    else:
      Logger.log('e', 'Could not upload print.')

  def _on_print_job_upload_progress(self, bytes_sent: int,
                                    bytes_total: int) -> None:
    """Called periodically by Cura to update the upload progress.

    Args:
      bytes_sent: Number of bytes already sent to the printer.
      bytes_total: Total bytes to be sent.
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
    """Called if there was an error to communicate the printer to start
    printing."""
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
        3)  # Make sure the output device gets selected above local file output.
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
    self._monitor_view_qml_path = os.path.join(
        plugin_path, 'resources', 'qml', 'MonitorStage.qml')

  @staticmethod
  def _build_printer_conf_model() -> PrinterConfigurationModel:
    """Returns printer's configuration model."""
    printer_configuration_model = PrinterConfigurationModel()
    extruder_conf_model = ExtruderConfigurationModel()
    extruder_conf_model.setPosition(0)
    printer_configuration_model.setExtruderConfigurations([extruder_conf_model])
    printer_configuration_model.setPrinterType('type')
    return printer_configuration_model

  def _build_printer_output_model(self) -> PrinterOutputModel:
    """Returns printer Output Model for this device."""
    printer_output_model = PrinterOutputModel(
        output_controller=self._printer_output_controller,
        number_of_extruders=_NUM_EXTRUDERS)
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
        self._requested_cancel_print = False  # Fulfilled.
        self.cancelPrintRequestChanged.emit()
    elif printer_status_model.state == MPSM2PrinterStatusModel.State.PRINTING:
      self._printer_output_model.updateState('printing')
      # It should be anything but inactive states:
      # 'pausing', 'paused', 'resuming', 'wait_cleanup'.
      self._print_job_model.updateState('active')
      self._print_job_model.update_progress(printer_status_model.progress)
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
      self, model: MPSM2PrinterStatusModel) -> None:
    """Updates temperatures in the printer's output model.

    Args:
      model: Parsed model from printer's status response.
    """
    self._printer_output_model.extruders[0].updateHotendTemperature(
        float(model.hotend_temperature))
    self._update_historical_temperatures(
        model.hotend_temperature,
        model.bed_temperature)
    self._printer_output_model.extruders[0].updateTargetHotendTemperature(
        float(model.target_hotend_temperature))
    self._printer_output_model.updateBedTemperature(
        float(model.bed_temperature))
    self._printer_output_model.updateTargetBedTemperature(
        float(model.target_bed_temperature))
    if self._requested_hotend_temperature == model.target_hotend_temperature:
      self._requested_hotend_temperature = None
      self.hasTargetHotendInProgressChanged.emit()
    if self._requested_bed_temperature == model.target_bed_temperature:
      self._requested_bed_temperature = None
      self.hasTargetBedInProgressChanged.emit()

  def _update_historical_temperatures(
      self, hotend_temperature: int, bed_temperature: int) -> None:
    """Updates data points to plot temperatures over time.

    Args:
      hotend_temperature: Current hotend temperature in Celsius.
      bed_temperature: Current bed temperature in Celsius.
    """
    self._historical_hotend_temps.append(hotend_temperature)
    if len(self._historical_hotend_temps) > self.NUM_DATA_POINTS:
      self._historical_hotend_temps.pop(0)
    self._historical_bed_temps.append(bed_temperature)
    if len(self._historical_bed_temps) > self.NUM_DATA_POINTS:
      self._historical_bed_temps.pop(0)
