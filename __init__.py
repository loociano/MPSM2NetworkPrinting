from .src import MPSM2OutputDevicePlugin


def getMetaData():
    return {}


def register(app):
    return {
        "output_device": MPSM2OutputDevicePlugin.MPSM2OutputDevicePlugin(),
    }
