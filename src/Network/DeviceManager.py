"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
from typing import Optional, Callable, List, cast

from PyQt5.QtCore import pyqtSignal, QObject

from UM import i18nCatalog
from UM.Logger import Logger
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Signal import Signal

from cura.CuraApplication import CuraApplication
from cura.PrinterOutput.PrinterOutputDevice import ConnectionType
from cura.Settings.CuraStackBuilder import CuraStackBuilder
from cura.Settings.GlobalStack import GlobalStack

from .ApiClient import ApiClient
from .PrinterHeartbeat import PrinterHeartbeat
from ..MPSM2NetworkedPrinterOutputDevice \
  import MPSM2NetworkedPrinterOutputDevice


class DeviceManager(QObject):
  META_NETWORK_KEY = 'mpsm2_network_key'
  MANUAL_DEVICES_PREFERENCE_KEY = 'mpsm2networkprinting/manual_instances'
  I18N_CATALOG = i18nCatalog('cura')

  discoveredDevicesChanged = Signal()
  manualAddressChanged = pyqtSignal(str)
  onPrinterUpload = pyqtSignal(bool)

  def __init__(self) -> None:
    super().__init__()
    self._discovered_devices = {}
    self._machines = {}
    self._output_device_manager = CuraApplication.getInstance() \
      .getOutputDeviceManager()

    self.heartbeat_thread = PrinterHeartbeat()
    self.manualAddressChanged \
      .connect(self.heartbeat_thread.set_printer_ip_address)
    self.onPrinterUpload.connect(self.heartbeat_thread.handle_printer_busy)
    self.heartbeat_thread.heartbeatSignal.connect(self._on_printer_heartbeat)
    ContainerRegistry.getInstance().containerRemoved.connect(
        self._on_printer_container_removed)

  def start(self) -> None:
    Logger.log('d', 'Starting Device Manager.')
    for address in self._get_stored_manual_addresses():
      self.add_manual_device(address)
      self.manualAddressChanged.emit(address)

  def stop(self) -> None:
    Logger.log('d', 'Stopping Device Manager.')
    for instance_name in list(self._discovered_devices):
      self._on_discovered_device_removed(instance_name)

  def start_discovery(self) -> None:
    self.stop()
    self.start()

  def add_manual_device(
      self, address: str,
      callback: Optional[Callable[[bool, str], None]] = None) -> None:
    Logger.log('d', 'Adding manual device with address: %s', address)
    api_client = ApiClient(address, lambda error: Logger.log('e', str(error)))
    api_client.get_printer_status(
        lambda response: self._on_printer_status_response(response, address,
                                                          callback))

  def remove_manual_device(self, device_id: str,
                           address: Optional[str] = None) -> None:
    Logger.log('d', 'Removing manual device with device_id: %s and address: %s',
               device_id, address)
    if device_id not in self._discovered_devices and address is not None:
      device_id = DeviceManager._get_device_id(address)

    if device_id in self._discovered_devices:
      address = address or self._discovered_devices[device_id].ipAddress
      self._on_discovered_device_removed(device_id)

    if address in self._get_stored_manual_addresses():
      self._remove_stored_manual_address(address)

    if self.heartbeat_thread.isRunning():
      self.heartbeat_thread.exit()

    self._machines = {}

  def refresh_connections(self) -> None:
    Logger.log('d', 'Refreshing connections.')
    self._connect_to_active_machine()

  def _on_printer_container_removed(self, container) -> None:
    if container.getName() == 'Monoprice Select Mini V2':
      device_ids = set(self._discovered_devices.keys())
      # FIXME: this is a simplification.
      for device_id in device_ids:
        self.remove_manual_device(device_id)

  def _connect_to_active_machine(self) -> None:
    Logger.log('d', 'Connecting to active machine.')
    active_machine = CuraApplication.getInstance().getGlobalContainerStack()
    if not active_machine:
      return

    if not self.heartbeat_thread.isRunning():
      self.heartbeat_thread.start()
    output_device_manager = \
      CuraApplication.getInstance().getOutputDeviceManager()
    stored_device_id = active_machine.getMetaDataEntry(self.META_NETWORK_KEY)
    for device in self._discovered_devices.values():
      if device.key == stored_device_id:
        self._connect_to_output_device(device, active_machine)
      elif device.key in output_device_manager.getOutputDeviceIds():
        output_device_manager.removeOutputDevice(device.key)

  def _on_printer_status_response(
      self, response, address: str,
      callback: Optional[Callable[[bool, str], None]] = None) -> None:
    if response is None and callback is not None:
      CuraApplication.getInstance().callLater(callback, False, address)
      return

    Logger.log('d', 'Received response from printer on address %s: %s.',
               address, response)
    device = MPSM2NetworkedPrinterOutputDevice(
      DeviceManager._get_device_id(address), address)
    device.onPrinterUpload.connect(self.onPrinterUpload)
    device.update_printer_status(response)
    device.printerStatusChanged.emit()

    discovered_printers_model = \
      CuraApplication.getInstance().getDiscoveredPrintersModel()
    discovered_printers_model.addDiscoveredPrinter(
        ip_address=address,
        key=device.getId(),
        name=device.getName(),
        create_callback=self._create_machine,
        machine_type=device.printerType,
        device=device)

    self._discovered_devices[device.getId()] = device
    self.discoveredDevicesChanged.emit()
    self._connect_to_active_machine()
    self._store_manual_address(address)
    self.manualAddressChanged.emit(address)
    if callback is not None:
      CuraApplication.getInstance().callLater(callback, True, address)

  def _on_discovered_device_removed(self, device_id: str) -> None:
    Logger.log('d', 'Removing discovered device with device_id: %s', device_id)
    device = self._discovered_devices.pop(device_id, None)
    if not device:
      return
    device.close()
    CuraApplication.getInstance().getDiscoveredPrintersModel() \
      .removeDiscoveredPrinter(device.address)
    self.discoveredDevicesChanged.emit()

  def _create_machine(self, device_id: str) -> None:
    Logger.log('d', 'Creating machine.')
    device = self._discovered_devices.get(device_id)
    if device is None:
      return

    if self._machines.get(device_id) is None:
      new_machine = CuraStackBuilder.createMachine(device.name,
                                                   device.printerType)
      if not new_machine:
        Logger.log('e', 'Failed to create a new machine')
        return
      new_machine.setMetaDataEntry(self.META_NETWORK_KEY, device.key)
      CuraApplication.getInstance().getMachineManager().setActiveMachine(
          new_machine.getId())
      self._connect_to_output_device(device, new_machine)
      if not self.heartbeat_thread.isRunning():
        self.heartbeat_thread.start()
      self._machines[device_id] = new_machine

  def _store_manual_address(self, address: str) -> None:
    Logger.log('d', 'Storing address %s in user preferences', address)
    stored_addresses = self._get_stored_manual_addresses()
    if address in stored_addresses:
      return  # Prevent duplicates.
    if len(stored_addresses) == 1 and not stored_addresses[0]:
      new_value = address
    else:
      stored_addresses.append(address)
      new_value = ','.join(stored_addresses)
    CuraApplication.getInstance().getPreferences().setValue(
        self.MANUAL_DEVICES_PREFERENCE_KEY, new_value)

  def _remove_stored_manual_address(self, address: str) -> None:
    Logger.log('d', 'Removing address %s from user preferences.', address)
    stored_addresses = self._get_stored_manual_addresses()
    try:
      stored_addresses.remove(address)  # Can throw a ValueError
      new_value = ','.join(stored_addresses)
      CuraApplication.getInstance().getPreferences().setValue(
          self.MANUAL_DEVICES_PREFERENCE_KEY, new_value)
    except ValueError:
      Logger.log(
          'w',
          'Could not remove address from stored_addresses, it was not there')

  def _get_stored_manual_addresses(self) -> List[str]:
    preferences = CuraApplication.getInstance().getPreferences()
    preferences.addPreference(self.MANUAL_DEVICES_PREFERENCE_KEY, '')
    manual_instances = preferences.getValue(
        self.MANUAL_DEVICES_PREFERENCE_KEY).split(',')
    return manual_instances

  def _connect_to_output_device(self, device: MPSM2NetworkedPrinterOutputDevice,
                                machine: GlobalStack) -> None:
    Logger.log('d', 'Connecting to Output Device with key: %s.', device.key)
    machine.setName(device.name)
    machine.setMetaDataEntry(self.META_NETWORK_KEY, device.key)
    machine.setMetaDataEntry('group_name', device.name)
    machine.addConfiguredConnectionType(device.connectionType.value)

    if not device.isConnected():
      device.connect()

    output_device_manager = \
      CuraApplication.getInstance().getOutputDeviceManager()
    if device.key not in output_device_manager.getOutputDeviceIds():
      output_device_manager.addOutputDevice(device)

  def _is_discovered(self, address: str) -> MPSM2NetworkedPrinterOutputDevice:
    return self._discovered_devices.get(DeviceManager._get_device_id(address))

  def _on_printer_heartbeat(self, address: str, raw_response: str) -> None:
    device = cast(
        MPSM2NetworkedPrinterOutputDevice,
        self._discovered_devices.get(DeviceManager._get_device_id(address)))
    if device and raw_response == 'timeout':
      if not device.is_busy():
        self.stop()
        return
    if not device:
      self.start()
    else:
      device.update_printer_status(raw_response)
      device.printerStatusChanged.emit()

  @staticmethod
  def _get_device_id(address: str) -> str:
    return 'manual:{}'.format(address)
