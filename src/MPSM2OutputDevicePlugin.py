"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
from typing import Optional, Callable

from UM.Signal import Signal
from UM.OutputDevice.OutputDeviceManager import ManualDeviceAdditionAttempt
from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin

from cura.CuraApplication import CuraApplication

from .Network.DeviceManager import DeviceManager


class MPSM2OutputDevicePlugin(OutputDevicePlugin):
  """Plugin enables network interoperability with Monoprice Select Mini V2
  printers."""

  # Signal emitted when the list of discovered devices changed. Used by printer
  # action in this plugin.
  discoveredDevicesChanged = Signal()

  def __init__(self) -> None:
    super().__init__()
    self._device_manager = DeviceManager()
    self._device_manager.discoveredDevicesChanged \
      .connect(self.discoveredDevicesChanged)
    CuraApplication.getInstance().globalContainerStackChanged \
      .connect(self.refreshConnections)

  # Overrides
  def start(self) -> None:
    self._device_manager.start()

  # Overrides
  def stop(self) -> None:
    self._device_manager.stop()

  # Overrides
  def startDiscovery(self) -> None:
    self._device_manager.start_discovery()

  # Overrides
  def refreshConnections(self) -> None:
    self._device_manager.refresh_connections()

  # Overrides
  def canAddManualDevice(self,
                         address: str = '') -> ManualDeviceAdditionAttempt:
    return ManualDeviceAdditionAttempt.PRIORITY

  # Overrides
  def addManualDevice(
      self, address: str,
      callback: Optional[Callable[[bool, str], None]] = None) -> None:
    self._device_manager.add_manual_device(address, callback)

  # Overrides
  def removeManualDevice(self, key: str, address: Optional[str] = None) -> None:
    self._device_manager.remove_manual_device(key, address)
