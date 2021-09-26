"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
from typing import Optional, Callable, List, cast

from PyQt5.QtCore import pyqtSignal, QObject

from UM import i18nCatalog
from UM.Logger import Logger
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.Interfaces import ContainerInterface
from UM.Signal import Signal
# pylint:disable=import-error
from cura.CuraApplication import CuraApplication
from cura.Settings.CuraStackBuilder import CuraStackBuilder
from cura.Settings.GlobalStack import GlobalStack
# pylint:disable=relative-beyond-top-level
from .ApiClient import ApiClient
from .PrinterHeartbeat import PrinterHeartbeat
from ..MPSM2NetworkedPrinterOutputDevice import MPSM2NetworkedPrinterOutputDevice

_METADATA_MPSM2_KEY = 'mpsm2_network_key'
_MANUAL_DEVICES_PREFERENCE_KEY = 'mpsm2networkprinting/manual_instances'


def _get_stored_manual_addresses() -> List[str]:
  """Returns list of IP address from Cura user's preferences."""
  preferences = CuraApplication.getInstance().getPreferences()
  preferences.addPreference(_MANUAL_DEVICES_PREFERENCE_KEY, '')
  if not preferences.getValue(_MANUAL_DEVICES_PREFERENCE_KEY):
    return []
  return preferences.getValue(_MANUAL_DEVICES_PREFERENCE_KEY).split(',')


def _get_device_id(address: str) -> str:
  """Returns device ID given an IP address."""
  return 'manual:{}'.format(address)


def _get_address(device_id: str) -> Optional[str]:
  """Returns IP address given a device ID. None if device ID is not found."""
  if not device_id:
    return None
  return device_id[len('manual:'):]


def _connect_to_output_device(device: MPSM2NetworkedPrinterOutputDevice,
                              machine: GlobalStack) -> None:
  """Connects to Output Device.

  This makes Cura display the printer as online.

  Args:
    device: Monoprice Select Mini V2 instance.
  """
  Logger.log('d', 'Connecting to Output Device with key: %s.', device.key)
  machine.addConfiguredConnectionType(device.connectionType.value)
  if not device.isConnected():
    device.connect()
  output_device_manager = (
      CuraApplication.getInstance().getOutputDeviceManager())
  if device.key not in output_device_manager.getOutputDeviceIds():
    output_device_manager.addOutputDevice(device)


def _store_manual_address(address: str) -> None:
  """Stores IP address in Cura user's preferences.

  Args:
    address: Printer's IP address.
  """
  Logger.log('d', 'Storing address %s in user preferences.', address)
  stored_addresses = _get_stored_manual_addresses()
  if address in stored_addresses:
    return  # Prevent duplicates.
  if len(stored_addresses) == 1 and not stored_addresses[0]:
    new_value = address
  else:
    stored_addresses.append(address)
    new_value = ','.join(stored_addresses)
  CuraApplication.getInstance().getPreferences().setValue(
      _MANUAL_DEVICES_PREFERENCE_KEY, new_value)


def _remove_stored_manual_address(address: str) -> None:
  """Removes IP address from Cura user's preferences.

  Args:
    address: Printer's IP address.
  """
  Logger.log('d', 'Removing address %s from user preferences.', address)
  stored_addresses = _get_stored_manual_addresses()
  try:
    stored_addresses.remove(address)  # Can throw ValueError.
    new_value = ','.join(stored_addresses)
    CuraApplication.getInstance().getPreferences().setValue(
        _MANUAL_DEVICES_PREFERENCE_KEY, new_value)
  except ValueError:
    Logger.log(
        'w',
        'Could not remove address from stored_addresses, it was not there.')


class DeviceManager(QObject):
  """Discovers and manages Monoprice Select Mini V2 printers over the
  network."""
  I18N_CATALOG = i18nCatalog('cura')

  discoveredDevicesChanged = Signal()
  onPrinterUpload = pyqtSignal(bool)

  def __init__(self) -> None:
    super().__init__()
    self._discovered_devices = {}
    self._background_threads = {}
    self._output_device_manager = (
        CuraApplication.getInstance().getOutputDeviceManager())
    ContainerRegistry.getInstance().containerRemoved.connect(
        self._on_printer_container_removed)
    self._add_manual_device_in_progress = False

  def start(self) -> None:
    Logger.log('d', 'Starting Device Manager.')
    for address in _get_stored_manual_addresses():
      self._create_heartbeat_thread(address)

  def stop(self) -> None:
    Logger.log('d', 'Stopping Device Manager.')
    for instance_name in list(self._discovered_devices):
      self._on_discovered_device_removed(instance_name)

  def start_discovery(self) -> None:
    Logger.log('d', 'Start discovery.')
    self.stop()
    self.start()

  def connect_to_active_machine(self) -> None:
    """Connects to the active machine.

    If the active machine is not a networked Monoprice Select Mini V2 printer,
    it removes them as Output Device.
    """
    Logger.log('d', 'Connecting to active machine.')
    active_machine = CuraApplication.getInstance().getGlobalContainerStack()
    if not active_machine:
      return  # Should only occur on fresh installations of Cura.

    output_device_manager = (
        CuraApplication.getInstance().getOutputDeviceManager())
    stored_device_id = active_machine.getMetaDataEntry(_METADATA_MPSM2_KEY)
    for device in self._discovered_devices.values():
      if device.key == stored_device_id:
        _connect_to_output_device(device, active_machine)
      elif device.key in output_device_manager.getOutputDeviceIds():
        output_device_manager.removeOutputDevice(device.key)

  def add_device(
      self,
      address: str,
      callback: Optional[Callable[[bool, str], None]] = None) -> None:
    """Handles user-request to add a device by IP address.

    Args:
      address: Printer's IP address.
      callback: Called after requests completes.
    """
    Logger.log('d', 'Requesting to add device with address: %s.', address)
    self._add_manual_device_in_progress = True
    api_client = ApiClient(address)
    api_client.get_printer_status(
        lambda response: self._on_printer_status_response(
            response, address, callback),
        self._on_printer_status_error)

  def remove_device(self, device_id: Optional[str],
                    address: Optional[str] = None) -> None:
    """Handles user-request to delete a device.

    Args:
      device_id: Device identifier 'manual:<ip_address>'.
      address: Printer's IP address.
    """
    Logger.log('d', 'Removing manual device with device_id: %s and address: %s',
               device_id, address)
    if device_id not in self._discovered_devices and address is not None:
      device_id = _get_device_id(address)

    if device_id in self._discovered_devices:
      address = address or self._discovered_devices[device_id].ipAddress
      self._on_discovered_device_removed(device_id)

    if address in _get_stored_manual_addresses():
      _remove_stored_manual_address(address)

    if address in self._background_threads:
      Logger.log('d', 'Stopping background thread for address %s.', address)
      self._background_threads[address].stopBeat()
      self._background_threads[address].quit()
      del self._background_threads[address]

  def _create_heartbeat_thread(self, address: str) -> None:
    """Creates and starts a background thread to ping the printer status.

    Args
      address: printer's IP address.
    """
    Logger.log('d', 'Creating heartbeat thread for stored address: %s',
               address)
    heartbeat_thread = PrinterHeartbeat(address)
    heartbeat_thread.heartbeatSignal.connect(self._on_printer_heartbeat)
    self.onPrinterUpload.connect(heartbeat_thread.handle_printer_busy)
    heartbeat_thread.start()
    self._background_threads[address] = heartbeat_thread

  def _on_printer_container_removed(self,
                                    container: ContainerInterface) -> None:
    """Removes device if it is managed by this plugin.

    Called when the user deletes a printer.

    Args:
      container: deleted container.
    """
    device_id = container.getMetaDataEntry(_METADATA_MPSM2_KEY)
    self.remove_device(device_id, _get_address(device_id))

  def _on_printer_status_error(self) -> None:
    """Called when the printer status has error."""
    self._add_manual_device_in_progress = False

  def _on_printer_status_response(
      self, response, address: str,
      callback: Optional[Callable[[bool, str], None]] = None) -> None:
    """Called when the printer status requests completes.

    Args:
      response: Response to the status request. Can be 'timeout'.
      address: Printer's IP address.
      callback: Called after this function finishes.
    """
    self._add_manual_device_in_progress = False
    if response is None and callback is not None:
      CuraApplication.getInstance().callLater(callback, False, address)
      return

    Logger.log('d', 'Received response from printer on address %s: %s.',
               address, response)
    device = MPSM2NetworkedPrinterOutputDevice(_get_device_id(address), address)
    device.onPrinterUpload.connect(self.onPrinterUpload)
    device.update_printer_status(response)
    discovered_printers_model = (
        CuraApplication.getInstance().getDiscoveredPrintersModel())
    discovered_printers_model.addDiscoveredPrinter(
        ip_address=address,
        key=device.getId(),
        name=device.getName(),
        create_callback=self._create_machine,
        machine_type=device.printerType,
        device=device)
    _store_manual_address(address)
    self._discovered_devices[device.getId()] = device
    self.discoveredDevicesChanged.emit()
    self.connect_to_active_machine()
    if callback is not None:
      CuraApplication.getInstance().callLater(callback, True, address)

  def _on_discovered_device_removed(self, device_id: str) -> None:
    """Called when a discovered device by this plugin is removed.

    Args:
      device_id: device identifier.
    """
    Logger.log('d', 'Removing discovered device with device_id: %s', device_id)
    device = self._discovered_devices.pop(device_id, None)
    if not device:
      return
    device.close()
    (CuraApplication.getInstance()
     .getDiscoveredPrintersModel().removeDiscoveredPrinter(device.address))
    self.discoveredDevicesChanged.emit()

  def _create_machine(self, device_id: str) -> None:
    """Creates a machine. Called when user adds a discovered machine.

    Args:
      device_id: device identifier.
    """
    Logger.log('d', 'Creating machine with device id %s.', device_id)
    device = cast(MPSM2NetworkedPrinterOutputDevice,
                  self._discovered_devices.get(device_id))
    if device is None:
      return

    machine_manager = CuraApplication.getInstance().getMachineManager()
    machine = machine_manager.getMachine(
        'monoprice_select_mini_v2', {_METADATA_MPSM2_KEY: device_id})
    if machine is None:
      new_machine = CuraStackBuilder.createMachine(
          device.name, device.printerType)
      if not new_machine:
        Logger.log('e', 'Failed to create a new machine.')
        return
      new_machine.setMetaDataEntry('group_name', device.name)
      new_machine.setMetaDataEntry(_METADATA_MPSM2_KEY, device.key)
      CuraApplication.getInstance().getMachineManager().setActiveMachine(
          new_machine.getId())
      _connect_to_output_device(device, new_machine)
      self._create_heartbeat_thread(device.ipAddress)

  def _on_printer_heartbeat(self, address: str, response: str) -> None:
    """Called when background heartbeat was received. Includes timeout.

    Args:
      address: IP address
      response: HTTP body response to inquiry request.
    """
    device = cast(
        MPSM2NetworkedPrinterOutputDevice,
        self._discovered_devices.get(_get_device_id(address)))
    if response == 'timeout':
      if (device
          and device.isConnected()
          and not device.is_uploading()
          and not self._add_manual_device_in_progress):
        # Request timeout is expected during job upload.
        Logger.log('d', 'Discovered device timed out. Stopping device.')
        device.close()
      return

    if not device:
      self._on_printer_status_response(response, address)
      return

    device = cast(
        MPSM2NetworkedPrinterOutputDevice,
        self._discovered_devices.get(_get_device_id(address)))
    if not device.isConnected():
      Logger.log('d', 'Printer at %s is up again. Reconnecting.', address)
      self.connect_to_active_machine()
      self.discoveredDevicesChanged.emit()
    device.update_printer_status(response)
