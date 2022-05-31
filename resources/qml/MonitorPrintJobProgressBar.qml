// Copyright 2020 Luc Rubio <luc@loociano.com>
// Plugin is licensed under the GNU Lesser General Public License v3.0.
import QtQuick 2.3
import QtQuick.Controls 2.0
import UM 1.3 as UM

Item {
    property var printJob: null
    width: childrenRect.width
    height: UM.Theme.getSize('monitor_text_line').height

    UM.ProgressBar {
        id: progressBar
        anchors {
            verticalCenter: parent.verticalCenter
            left: parent.left
        }
        value: printJob ? printJob.progress / 100 : 0
        width: UM.Theme.getSize('monitor_progress_bar').width
    }

    Label {
        id: percentLabel
        anchors {
            left: progressBar.right
            leftMargin: UM.Theme.getSize('monitor_margin').width
            verticalCenter: parent.verticalCenter
        }
        text: printJob ? printJob.progress + '%' : '0%'
        color: UM.Theme.getColor('monitor_text_primary')
        width: contentWidth
        font: UM.Theme.getFont('default')
        height: UM.Theme.getSize('monitor_text_line').height
        verticalAlignment: Text.AlignVCenter
        renderType: Text.NativeRendering
    }

    Label {
        anchors {
            top: progressBar.bottom
            left: parent.left
        }
        text: printJob && printJob.estimated_time_left
            ? printJob.estimated_time_left
            : catalog.i18nc('@label', 'Calculating remaining time...')
        color: UM.Theme.getColor('monitor_text_primary')
        font: UM.Theme.getFont('default')
        height: UM.Theme.getSize('monitor_text_line').height
        verticalAlignment: Text.AlignVCenter
        renderType: Text.NativeRendering
    }
}
