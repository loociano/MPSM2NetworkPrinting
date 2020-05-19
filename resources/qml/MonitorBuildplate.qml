// Copyright 2020 Luc Rubio <luc@loociano.com>
// Plugin is licensed under the GNU Lesser General Public License v3.0.
import QtQuick 2.2
import QtQuick.Controls 2.0
import UM 1.3 as UM

Item {
    property var bedTemperature: null
    property var targetBedTemperature: null
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
        width: Math.max(targetBedTemperatureLabel.contentWidth, 36 * screenScaleFactor)
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
}
