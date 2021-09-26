"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
from typing import Optional, Callable

from UM.Signal import Signal
from UM.OutputDevice.OutputDeviceManager import ManualDeviceAdditionAttempt
from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin

# pylint:disable=import-error
from cura.CuraApplication import CuraApplication

# pylint:disable=relative-beyond-top-level
from .network.DeviceManager import DeviceManager


class MPSM2OutputDevicePlugin(OutputDevicePlugin):
  """Plugin enables network interoperability with Monoprice Select Mini V2
  printers."""

  # Signal emitted when the list of discovered devices changed. Used by printer
  # action in this plugin.
  discoveredDevicesChanged = Signal()

  def __init__(self) -> None:
    super().__init__()
    self._device_manager = DeviceManager()
    (self._device_manager.discoveredDevicesChanged
     .connect(self.discoveredDevicesChanged))
    (CuraApplication.getInstance().globalContainerStackChanged
     .connect(self.refreshConnections))

  def start(self) -> None:
    """See base class."""
    self._device_manager.start()

  def stop(self) -> None:
    """See base class."""
    self._device_manager.stop()

  def startDiscovery(self) -> None:
    """See base class."""
    self._device_manager.start_discovery()

  def refreshConnections(self) -> None:
    """See base class."""
    self._device_manager.connect_to_active_machine()

  def canAddManualDevice(self,
                         address: str = '') -> ManualDeviceAdditionAttempt:
    """See base class."""
    return ManualDeviceAdditionAttempt.PRIORITY

  def addManualDevice(
      self, address: str,
      callback: Optional[Callable[[bool, str], None]] = None) -> None:
    """See base class."""
    self._device_manager.add_device(address, callback)

  def removeManualDevice(self, key: str, address: Optional[str] = None) -> None:
    """See base class."""
    self._device_manager.remove_device(key, address)
