// Copyright 2020 Luc Rubio <luc@loociano.com>
// Plugin is licensed under the GNU Lesser General Public License v3.0.
import QtQuick 2.2
import QtQuick.Controls 2.0
import UM 1.3 as UM
import Cura 1.5 as Cura

Item {
    property var hotendTemperature : null // int
    property var targetHotendTemperature : null // int
    property int max_hotend_temperature : OutputDevice.max_hotend_temperature
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
            text: hotendTemperature !== '' ? hotendTemperature + 'ºC' : ''
            visible: text
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
            visible: text
            height: parent.height
            verticalAlignment: Text.AlignVCenter
            renderType: Text.NativeRendering
        }
    }

    Item {
        id: targetHotendTemperatureInputFields
        height: childrenRect.height
        anchors {
            top: parent.top
            left: targetHotendTemperatureWrapper.right
            leftMargin: 48 * screenScaleFactor
        }

        Cura.TextField {
            id: targetHotendTemperatureField
            width: 48 * screenScaleFactor
            height: setTargetHotendTemperatureButton.height
            anchors {
                verticalCenter: setTargetHotendTemperatureButton.verticalCenter
                left: parent.left
            }
            signal invalidInputDetected()
            onInvalidInputDetected: invalidTargetHotendTemperatureLabel.visible = true
            onTextEdited: invalidTargetHotendTemperatureLabel.visible = false
            maximumLength: 3
            placeholderText: targetHotendTemperature !== '' ? targetHotendTemperature : 0
            enabled: !OutputDevice.isUploading
            onAccepted: setTargetHotendTemperatureButton.clicked()
        }

        Label {
            id: invalidTargetHotendTemperatureLabel
            anchors {
                top: targetHotendTemperatureField.bottom
                topMargin: UM.Theme.getSize('narrow_margin').height
                left: parent.left
            }
            visible: false
            text: catalog.i18nc('@text', 'Temperature must be between 0ºC and ' + max_hotend_temperature + 'ºC.')
            font: UM.Theme.getFont('default')
            color: UM.Theme.getColor('error')
            renderType: Text.NativeRendering
        }

        Cura.SecondaryButton {
            id: setTargetHotendTemperatureButton
            anchors {
                top: parent.top
                left: targetHotendTemperatureField.right
                leftMargin: UM.Theme.getSize('default_margin').width
            }
            text: catalog.i18nc('@button', 'Set Target')
            enabled: !OutputDevice.isUploading
            busy: OutputDevice.has_target_hotend_in_progress
            onClicked: {
                if (!OutputDevice.isValidHotendTemperature(targetHotendTemperatureField.text)) {
                    targetHotendTemperatureField.invalidInputDetected();
                    return;
                }
                if (!OutputDevice.has_target_hotend_in_progress) {
                    OutputDevice.setTargetHotendTemperature(parseInt(targetHotendTemperatureField.text));
                }
            }
        }
    }
}
