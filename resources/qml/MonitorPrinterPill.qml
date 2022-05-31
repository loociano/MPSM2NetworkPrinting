// Copyright 2020 Luc Rubio <luc@loociano.com>
// Plugin is licensed under the GNU Lesser General Public License v3.0.
import QtQuick 2.2
import QtQuick.Controls 2.0
import UM 1.2 as UM

Item {
    id: monitorPrinterPill
    property var text: ''

    implicitHeight: 18 * screenScaleFactor
    implicitWidth: Math.max(printerNameLabel.contentWidth + 12 * screenScaleFactor, 36 * screenScaleFactor)

    Rectangle {
        id: background
        anchors.fill: parent
        color: printerNameLabel.visible ? UM.Theme.getColor('monitor_printer_family_tag') : UM.Theme.getColor('monitor_skeleton_loading')
        radius: 2 * screenScaleFactor
    }

    Label {
        id: printerNameLabel
        anchors.centerIn: parent
        color: UM.Theme.getColor('monitor_text_primary')
        text: monitorPrinterPill.text
        font.pointSize: 10
        visible: monitorPrinterPill.text !== ''
        renderType: Text.NativeRendering
    }
}
