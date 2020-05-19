// Copyright 2020 Luc Rubio <luc@loociano.com>
// Plugin is licensed under the GNU Lesser General Public License v3.0.
import QtQuick 2.2
import QtQuick.Controls 2.0
import UM 1.3 as UM

Item {
    property var hotendTemperature : null // int
    property var targetHotendTemperature : null // int
    height: 40 * screenScaleFactor
    width: childrenRect.width

    MonitorIconExtruder {
        id: extruderIcon
        color: 'orange'
        position: 0
    }

    Rectangle {
        id: hotendTemperatureWrapper
        anchors {
            left: extruderIcon.right
            leftMargin: 12 * screenScaleFactor
        }
        color: hotendTemperatureLabel.visible > 0 ? 'transparent' : UM.Theme.getColor('monitor_skeleton_loading')
        height: 18 * screenScaleFactor
        width: Math.max(hotendTemperatureLabel.contentWidth, 60 * screenScaleFactor)
        radius: 2 * screenScaleFactor

        Label {
            id: hotendTemperatureLabel
            color: UM.Theme.getColor('monitor_text_primary')
            elide: Text.ElideRight
            font: UM.Theme.getFont('large_bold')
            text: hotendTemperature + 'ºC'
            visible: hotendTemperature !== 0
            height: parent.height
            verticalAlignment: Text.AlignVCenter
            renderType: Text.NativeRendering
        }
    }

    Rectangle {
        id: targetHotendTemperatureWrapper
        anchors {
            left: hotendTemperatureWrapper.left
            bottom: parent.bottom
        }
        color: targetHotendTemperatureLabel.visible > 0 ? 'transparent' : UM.Theme.getColor('monitor_skeleton_loading')
        height: 18 * screenScaleFactor
        width: Math.max(targetHotendTemperatureLabel.contentWidth, 36 * screenScaleFactor)
        radius: 2 * screenScaleFactor

        Label {
            id: targetHotendTemperatureLabel
            color: UM.Theme.getColor('monitor_text_primary')
            elide: Text.ElideRight
            font: UM.Theme.getFont('default')
            text: targetHotendTemperature !== '' ? 'Target: ' + targetHotendTemperature + 'ºC' : ''
            visible: text !== ''
            height: parent.height
            verticalAlignment: Text.AlignVCenter
            renderType: Text.NativeRendering
        }
    }
}
