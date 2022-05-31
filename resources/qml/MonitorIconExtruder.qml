// Copyright 2020 Luc Rubio <luc@loociano.com>
// Plugin is licensed under the GNU Lesser General Public License v3.0.
import QtQuick 2.2
import QtQuick.Controls 2.0
import UM 1.3 as UM

Item {
    property int position: 0
    property int size: 32 * screenScaleFactor
    property string iconSource: '../svg/icons/extruder.svg'
    height: size
    width: size

    Image {
        id: icon
        anchors.fill: parent
        source: iconSource
        width: size
    }

    Label {
        id: positionLabel
        font: UM.Theme.getFont('small')
        color: UM.Theme.getColor('monitor_text_primary')
        height: Math.round(size / 2)
        horizontalAlignment: Text.AlignHCenter
        text: position + 1
        verticalAlignment: Text.AlignVCenter
        width: Math.round(size / 2)
        x: Math.round(size * 0.25)
        y: Math.round(size * 0.15625)
        visible: position >= 0
        renderType: Text.NativeRendering
    }
}
