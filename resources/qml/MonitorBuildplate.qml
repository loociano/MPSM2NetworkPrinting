// Copyright 2020 Luc Rubio <luc@loociano.com>
// Plugin is licensed under the GNU Lesser General Public License v3.0.
import QtQuick 2.2
import QtQuick.Controls 2.0
import UM 1.3 as UM
import Cura 1.5 as Cura

// TODO: parameterize along with extruder counterpart.
Item {
    property var bedTemperature: null
    property var targetBedTemperature: null
    property int max_bed_temperature : OutputDevice.max_bed_temperature
    height: 40 * screenScaleFactor
    width: childrenRect.width

    UM.RecolorImage {
        id: buildplateIcon
        color: UM.Theme.getColor('monitor_icon_primary')
        source: '../svg/icons/buildplate.svg'
        width: 32 * screenScaleFactor
        height: width
        visible: buildplate
    }

    Rectangle {
        id: bedTemperatureWrapper
        anchors {
            left: buildplateIcon.right
            leftMargin: 12 * screenScaleFactor
        }
        color: bedTemperatureLabel.visible > 0 ? 'transparent' : UM.Theme.getColor('monitor_skeleton_loading')
        height: 18 * screenScaleFactor
        width: Math.max(bedTemperatureLabel.contentWidth, 60 * screenScaleFactor)
        radius: 2 * screenScaleFactor

        Label {
            id: bedTemperatureLabel
            color: UM.Theme.getColor('monitor_text_primary')
            elide: Text.ElideRight
            font: UM.Theme.getFont('large_bold')
            text: bedTemperature !== -1 ? bedTemperature + 'ºC' : ''
            visible: bedTemperature !== -1 // Default bed temperature in PrinterOutputModel
            height: 18 * screenScaleFactor
            verticalAlignment: Text.AlignVCenter
            renderType: Text.NativeRendering
        }
    }

    Rectangle {
        id: targetBedTemperatureWrapper
        anchors
        {
            left: bedTemperatureWrapper.left
            bottom: parent.bottom
        }
        color: targetBedTemperatureLabel.visible > 0 ? 'transparent' : UM.Theme.getColor('monitor_skeleton_loading')
        height: 18 * screenScaleFactor
        width: 36 * screenScaleFactor
        radius: 2 * screenScaleFactor

        Label {
            id: targetBedTemperatureLabel
            color: UM.Theme.getColor('monitor_text_primary')
            elide: Text.ElideRight
            font: UM.Theme.getFont('default')
            text: targetBedTemperature !== '' ? 'Target: ' + targetBedTemperature + 'ºC' : ''
            visible: text !== ''
            height: 18 * screenScaleFactor
            verticalAlignment: Text.AlignVCenter
            renderType: Text.NativeRendering
        }
    }

    Item {
        id: targetBedTemperatureInputFields
        height: childrenRect.height
        anchors {
            top: parent.top
            left: targetBedTemperatureWrapper.right
            leftMargin: 48 * screenScaleFactor
        }

        Cura.TextField {
            id: targetBedTemperatureField
            width: 48 * screenScaleFactor
            height: setTargetBedTemperatureButton.height
            anchors {
                verticalCenter: setTargetBedTemperatureButton.verticalCenter
                left: parent.left
            }
            signal invalidInputDetected()
            onInvalidInputDetected: invalidTargetBedTemperatureLabel.visible = true
            onTextEdited: invalidTargetBedTemperatureLabel.visible = false
            maximumLength: 2 // max bed temperature is 85.
            placeholderText: targetBedTemperature !== '' ? targetBedTemperature : 0
            enabled: !OutputDevice.isUploading
            onAccepted: setTargetBedTemperatureButton.clicked()
        }

        Label {
            id: invalidTargetBedTemperatureLabel
            anchors {
                top: targetBedTemperatureField.bottom
                topMargin: UM.Theme.getSize('narrow_margin').height
                left: parent.left
            }
            visible: false
            text: catalog.i18nc('@text', 'Temperature must be between 0ºC and ' + max_bed_temperature + 'ºC.')
            font: UM.Theme.getFont('default')
            color: UM.Theme.getColor('error')
            renderType: Text.NativeRendering
        }

        Cura.SecondaryButton {
            id: setTargetBedTemperatureButton
            anchors {
                top: parent.top
                left: targetBedTemperatureField.right
                leftMargin: UM.Theme.getSize('default_margin').width
            }
            text: catalog.i18nc('@button', 'Set Target')
            enabled: !OutputDevice.isUploading && !OutputDevice.has_target_bed_in_progress
            busy: OutputDevice.has_target_bed_in_progress
            onClicked: {
                if (!OutputDevice.isValidBedTemperature(targetBedTemperatureField.text)) {
                    targetBedTemperatureField.invalidInputDetected();
                    return;
                }
                if (!OutputDevice.has_target_bed_in_progress) {
                    OutputDevice.setTargetBedTemperature(parseInt(targetBedTemperatureField.text));
                }
            }
        }
    }
}
