# Copyright 2020 Luc Rubio <luc@loociano.com>
# Plugin is licensed under the GNU Lesser General Public License v3.0.
from typing import Optional, Callable, List

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
from ..MPSM2NetworkedPrinterOutputDevice import MPSM2NetworkedPrinterOutputDevice


class DeviceManager(QObject):
    META_NETWORK_KEY = 'mpsm2_network_key'
    MANUAL_DEVICES_PREFERENCE_KEY = 'mpsm2networkprinting/manual_instances'
    I18N_CATALOG = i18nCatalog('cura')

    discoveredDevicesChanged = Signal()
    manualAddressChanged = pyqtSignal(str)
    onPrinterUpload = pyqtSignal(bool)

    MPSM2_PROPERTIES = {
        b'name': b'Monoprice Select Mini V2',
        b'machine': b'Malyan M200',
        b'manual': b'true',
        b'printer_type': b'monoprice_select_mini_v2',
        b'firmware_version': b'Unknown',
    }

    def __init__(self) -> None:
        super().__init__()
        self._discovered_devices = {}
        self._machines = {}
        self._output_device_manager = CuraApplication.getInstance().getOutputDeviceManager()

        self.heartbeatThread = PrinterHeartbeat()
        self.manualAddressChanged.connect(self.heartbeatThread.setPrinterIpAddress)
        self.onPrinterUpload.connect(self.heartbeatThread.handlePrinterBusy)
        self.heartbeatThread.heartbeatSignal.connect(self._onPrinterHeartbeat)
        ContainerRegistry.getInstance().containerRemoved.connect(self._onPrinterContainerRemoved)

    def start(self) -> None:
        Logger.log('d', 'Starting Device Manager.')
        for address in self._getStoredManualAddresses():
            self.addManualDevice(address)
            self.manualAddressChanged.emit(address)

    def stop(self) -> None:
        Logger.log('d', 'Stopping Device Manager.')
        for instance_name in list(self._discovered_devices):
            self._onDiscoveredDeviceRemoved(instance_name)

    def startDiscovery(self) -> None:
        self.stop()
        self.start()

    def addManualDevice(self, address: str, callback: Optional[Callable[[bool, str], None]] = None) -> None:
        Logger.log('d', 'Adding manual device with address: %s', address)
        api_client = ApiClient(address, lambda error: Logger.log('e', str(error)))
        api_client.getPrinterStatus(lambda response: self._onPrinterStatusResponse(response, address, callback))

    def removeManualDevice(self, device_id: str, address: Optional[str] = None) -> None:
        Logger.log('d', 'Removing manual device with device_id: %s and address: %s', device_id, address)
        if device_id not in self._discovered_devices and address is not None:
            device_id = DeviceManager._getDeviceId(address)

        if device_id in self._discovered_devices:
            address = address or self._discovered_devices[device_id].ipAddress
            self._onDiscoveredDeviceRemoved(device_id)

        if address in self._getStoredManualAddresses():
            self._removeStoredManualAddress(address)

        if self.heartbeatThread.isRunning():
            self.heartbeatThread.exit()

        self._machines = {}

    def refreshConnections(self) -> None:
        Logger.log('d', 'Refreshing connections.')
        self._connectToActiveMachine()

    def _onPrinterContainerRemoved(self, container) -> None:
        if container.getName() == DeviceManager.MPSM2_PROPERTIES[b'name'].decode('utf-8'):
            device_ids = set(self._discovered_devices.keys())
            # FIXME: this is a simplification.
            for device_id in device_ids:
                self.removeManualDevice(device_id)

    def _connectToActiveMachine(self) -> None:
        Logger.log('d', 'Connecting to active machine.')
        active_machine = CuraApplication.getInstance().getGlobalContainerStack()
        if not active_machine:
            return

        if not self.heartbeatThread.isRunning():
            self.heartbeatThread.start()
        output_device_manager = CuraApplication.getInstance().getOutputDeviceManager()
        stored_device_id = active_machine.getMetaDataEntry(self.META_NETWORK_KEY)
        for device in self._discovered_devices.values():
            if device.key == stored_device_id:
                self._connectToOutputDevice(device, active_machine)
            elif device.key in output_device_manager.getOutputDeviceIds():
                output_device_manager.removeOutputDevice(device.key)

    def _onPrinterStatusResponse(self, response, address: str,
                                 callback: Optional[Callable[[bool, str], None]] = None) -> None:
        if response is None and callback is not None:
            CuraApplication.getInstance().callLater(callback, False, address)
            return

        Logger.log('d', 'Received response from printer on address %s: %s.', address, response)
        properties = DeviceManager.MPSM2_PROPERTIES.copy()
        properties[b'address'] = address.encode('utf-8')
        device = MPSM2NetworkedPrinterOutputDevice(DeviceManager._getDeviceId(address), address, properties,
                                                   ConnectionType.NetworkConnection)
        device.onPrinterUpload.connect(self.onPrinterUpload)
        device.updatePrinterStatus(response)
        device.printerStatusChanged.emit()

        discovered_printers_model = CuraApplication.getInstance().getDiscoveredPrintersModel()
        discovered_printers_model.addDiscoveredPrinter(
            ip_address=address,
            key=device.getId(),
            name=device.getName(),
            create_callback=self._createMachineFromDiscoveredDevice,
            machine_type=device.printerType,
            device=device)

        self._discovered_devices[device.getId()] = device
        self.discoveredDevicesChanged.emit()
        self._connectToActiveMachine()
        self._storeManualAddress(address)
        self.manualAddressChanged.emit(address)
        if callback is not None:
            CuraApplication.getInstance().callLater(callback, True, address)

    def _onDiscoveredDeviceRemoved(self, device_id: str) -> None:
        Logger.log('d', 'Removing discovered device with device_id: %s', device_id)
        device = self._discovered_devices.pop(device_id, None)
        if not device:
            return
        device.close()
        CuraApplication.getInstance().getDiscoveredPrintersModel().removeDiscoveredPrinter(device.address)
        self.discoveredDevicesChanged.emit()

    def _createMachineFromDiscoveredDevice(self, device_id: str) -> None:
        Logger.log('d', 'Creating machine.')
        device = self._discovered_devices.get(device_id)
        if device is None:
            return

        if self._machines.get(device_id) is None:
            new_machine = CuraStackBuilder.createMachine(device.name, device.printerType)
            if not new_machine:
                Logger.log('e', 'Failed to create a new machine')
                return
            new_machine.setMetaDataEntry(self.META_NETWORK_KEY, device.key)
            CuraApplication.getInstance().getMachineManager().setActiveMachine(new_machine.getId())
            self._connectToOutputDevice(device, new_machine)
            if not self.heartbeatThread.isRunning():
                self.heartbeatThread.start()
            self._machines[device_id] = new_machine

    def _storeManualAddress(self, address: str) -> None:
        Logger.log('d', 'Storing address %s in user preferences', address)
        stored_addresses = self._getStoredManualAddresses()
        if address in stored_addresses:
            return  # Prevent duplicates.
        if len(stored_addresses) == 1 and not stored_addresses[0]:
            new_value = address
        else:
            stored_addresses.append(address)
            new_value = ','.join(stored_addresses)
        CuraApplication.getInstance().getPreferences().setValue(self.MANUAL_DEVICES_PREFERENCE_KEY, new_value)

    def _removeStoredManualAddress(self, address: str) -> None:
        Logger.log('d', 'Removing address %s from user preferences.', address)
        stored_addresses = self._getStoredManualAddresses()
        try:
            stored_addresses.remove(address)  # Can throw a ValueError
            new_value = ','.join(stored_addresses)
            CuraApplication.getInstance().getPreferences().setValue(self.MANUAL_DEVICES_PREFERENCE_KEY, new_value)
        except ValueError:
            Logger.log('w', 'Could not remove address from stored_addresses, it was not there')

    def _getStoredManualAddresses(self) -> List[str]:
        preferences = CuraApplication.getInstance().getPreferences()
        preferences.addPreference(self.MANUAL_DEVICES_PREFERENCE_KEY, '')
        manual_instances = preferences.getValue(self.MANUAL_DEVICES_PREFERENCE_KEY).split(',')
        return manual_instances

    def _connectToOutputDevice(self, device: MPSM2NetworkedPrinterOutputDevice, machine: GlobalStack) -> None:
        Logger.log('d', 'Connecting to Output Device with key: %s.', device.key)
        machine.setName(device.name)
        machine.setMetaDataEntry(self.META_NETWORK_KEY, device.key)
        machine.setMetaDataEntry('group_name', device.name)
        machine.addConfiguredConnectionType(device.connectionType.value)

        if not device.isConnected():
            device.connect()

        output_device_manager = CuraApplication.getInstance().getOutputDeviceManager()
        if device.key not in output_device_manager.getOutputDeviceIds():
            output_device_manager.addOutputDevice(device)

    def _isDiscovered(self, address: str) -> MPSM2NetworkedPrinterOutputDevice:
        return self._discovered_devices.get(DeviceManager._getDeviceId(address))

    def _onPrinterHeartbeat(self, address: str, raw_response: str) -> None:
        device = self._discovered_devices.get(DeviceManager._getDeviceId(address))
        if device and raw_response == 'timeout':
            if not device.isBusy():
                self.stop()
                return
        if not device:
            self.start()
        else:
            device.updatePrinterStatus(raw_response)
            device.printerStatusChanged.emit()

    @staticmethod
    def _getDeviceId(address: str) -> str:
        return 'manual:{}'.format(address)
