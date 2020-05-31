# pylint:disable=invalid-name
"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
# pylint:disable=import-error
from .src import MPSM2OutputDevicePlugin


# pylint:disable=invalid-name
def getMetaData():
  """
  Returns:
    Plugin metadata.
    https://github.com/Ultimaker/Uranium/blob/master/docs/plugins.md
  """
  return {}


# pylint:disable=unused-argument
def register(app):
  """Registers the plugin."""
  return {
      "output_device": MPSM2OutputDevicePlugin.MPSM2OutputDevicePlugin(),
  }
