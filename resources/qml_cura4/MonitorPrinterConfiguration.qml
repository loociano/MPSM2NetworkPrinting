// Copyright 2020 Luc Rubio <luc@loociano.com>
// Plugin is licensed under the GNU Lesser General Public License v3.0.
import QtQuick 2.2
import QtQuick.Controls 2.0
import UM 1.3 as UM

Item {
    id: base
    property var extruder: null
    property var buildplate: null
    height: parent.height
    width: 450 * screenScaleFactor // Default size, but should be stretched to fill parent

    Column {
        spacing: 18 * screenScaleFactor

        MonitorExtruder {
            hotendTemperature: extruder.hotendTemperature
            targetHotendTemperature: extruder.targetHotendTemperature
            width: base.width
        }

        MonitorBuildplate {
            bedTemperature: buildplate[0]
            targetBedTemperature: buildplate[1]
            width: base.width
        }
    }
}
