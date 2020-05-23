// Copyright 2020 Luc Rubio <luc@loociano.com>
// Plugin is licensed under the GNU Lesser General Public License v3.0.
import QtQuick 2.2
import QtQuick.Controls 2.0
import UM 1.3 as UM
import Cura 1.5 as Cura

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

    Cura.TextField {
        id: targetHotendTemperatureField
        width: 48 * screenScaleFactor
        height: setTargetHotendTemperatureButton.height
        anchors {
            verticalCenter: parent.verticalCenter
            left: targetHotendTemperatureWrapper.right
            leftMargin: 48 * screenScaleFactor
        }
        // TODO: validation
        maximumLength: 3
        placeholderText: catalog.i18nc('@text', '210') // TODO
        enabled: true // TODO
        onAccepted: setTargetHotendTemperatureButton.clicked()
    }

    Cura.SecondaryButton {
        id: setTargetHotendTemperatureButton
        anchors {
            verticalCenter: parent.verticalCenter
            left: targetHotendTemperatureField.right
            leftMargin: 8 * screenScaleFactor
        }
        text: catalog.i18nc('@button', 'Set Target')
        enabled: true // TODO
        busy: OutputDevice.has_target_hotend_in_progress
        onClicked: {
            const temperature = targetHotendTemperatureField.text
            // TODO: validate
            if (!OutputDevice.has_target_hotend_in_progress) {
                OutputDevice.setTargetHotendTemperature(temperature)
            }
        }
    }
}
