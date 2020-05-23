// Copyright 2020 Luc Rubio <luc@loociano.com>
// Plugin is licensed under the GNU Lesser General Public License v3.0.
import QtQuick 2.3
import QtQuick.Controls 2.0
import QtQuick.Dialogs 1.1
import UM 1.3 as UM
import Cura 1.5 as Cura

Item {
    id: base
    property var printer: null
    property var borderSize: 1 * screenScaleFactor
    property var enabled: true
    width: 834 * screenScaleFactor
    height: childrenRect.height

    Rectangle {
        id: background
        anchors.fill: parent
        color: UM.Theme.getColor('monitor_card_background')
        border {
            color: UM.Theme.getColor('monitor_card_border')
            width: borderSize
        }
        radius: 2 * screenScaleFactor
    }

    Item {
        id: printerInfo
        width: parent.width
        height: 144 * screenScaleFactor

        Row {
            anchors {
                left: parent.left
                leftMargin: 36 * screenScaleFactor
                verticalCenter: parent.verticalCenter
            }
            spacing: 18 * screenScaleFactor

            Rectangle {
                id: printerImage
                width: 108 * screenScaleFactor
                height: 108 * screenScaleFactor
                color: printer ? 'transparent' : UM.Theme.getColor('monitor_skeleton_loading')
                radius: 8
                Image {
                    anchors.fill: parent
                    fillMode: Image.PreserveAspectFit
                    source: '../png/monoprice_select_mini_v2.png'
                    mipmap: true
                }
            }

            Item {
                anchors {
                    verticalCenter: parent.verticalCenter
                }
                width: 180 * screenScaleFactor
                height: childrenRect.height

                Rectangle {
                    id: printerNameLabel
                    color: printer ? 'transparent' : UM.Theme.getColor('monitor_skeleton_loading')
                    height: 18 * screenScaleFactor
                    width: parent.width
                    radius: 2 * screenScaleFactor

                    Label {
                        text: printer && printer.name ? printer.name : ''
                        color: UM.Theme.getColor('monitor_text_primary')
                        elide: Text.ElideRight
                        font: UM.Theme.getFont('large_bold')
                        width: parent.width
                        visible: printer
                        height: parent.height
                        verticalAlignment: Text.AlignVCenter
                        renderType: Text.NativeRendering
                    }
                }

                MonitorPrinterPill {
                    id: printerFamilyPill
                    anchors {
                        top: printerNameLabel.bottom
                        topMargin: 6 * screenScaleFactor
                        left: printerNameLabel.left
                    }
                    text: printer ? printer.type : ''
                }
            }
            MonitorPrinterConfiguration {
                anchors {
                    top: parent.top
                }
                height: 72 * screenScaleFactor
                extruder: {
                    if (printer) {
                        return printer.extruders[0]
                    }
                    return null
                }
                buildplate: {
                    if (printer) {
                        return [printer.bedTemperature, printer.targetBedTemperature]
                    }
                    return null
                }
            }
        }
    }

    Rectangle {
        id: divider
        anchors {
            top: printJobInfo.top
            left: printJobInfo.left
            right: printJobInfo.right
        }
        height: borderSize
        color: background.border.color
    }

    Rectangle {
        id: printJobInfo
        anchors {
            top: printerInfo.bottom
            topMargin: -borderSize * screenScaleFactor
        }
        border {
            color: 'transparent'
            width: borderSize
        }
        color: 'transparent'
        height: 84 * screenScaleFactor + borderSize
        width: parent.width

        Row {
            anchors {
                fill: parent
                topMargin: 12 * screenScaleFactor + borderSize
                bottomMargin: 12 * screenScaleFactor
                leftMargin: 36 * screenScaleFactor
            }
            height: childrenRect.height
            spacing: 18 * screenScaleFactor

            Label {
                id: printerStatus
                anchors {
                    verticalCenter: parent.verticalCenter
                }
                color: UM.Theme.getColor('monitor_text_primary')
                font: UM.Theme.getFont('medium')
                text: {
                    if (printer) {
                        switch(printer.state) {
                            case 'idle':
                                return catalog.i18nc('@label:status', 'Ready')
                            case 'printing':
                                return catalog.i18nc('@label:status', 'Printing')
                            case 'paused':
                                return catalog.i18nc('@label:status', 'Paused')
                        }
                    }
                    return ''
                }
                visible: text !== ''
                width: 108 * screenScaleFactor
                renderType: Text.NativeRendering
            }

            MonitorPrintJobProgressBar {
                anchors {
                    verticalCenter: parent.verticalCenter
                }
                printJob: printer && printer.activePrintJob
                visible: printer && printer.activePrintJob && (printer.activePrintJob.state === 'active' || printer.activePrintJob.state === 'paused')
            }
        }

        Button {
            id: pauseOrResumePrintButton
            anchors {
                verticalCenter: parent.verticalCenter
                right: cancelPrintButton.left
                rightMargin: 18 * screenScaleFactor
            }
            background: Rectangle {
                color: UM.Theme.getColor('monitor_secondary_button_shadow')
                radius: 2 * screenScaleFactor
                Rectangle {
                    anchors.fill: parent
                    anchors.bottomMargin: 2 * screenScaleFactor
                    color: pauseOrResumePrintButton.hovered ? UM.Theme.getColor('monitor_secondary_button_hover') : UM.Theme.getColor('monitor_secondary_button')
                    radius: 2 * screenScaleFactor
                }
            }
            contentItem: Label {
                anchors.fill: parent
                anchors.bottomMargin: 2 * screenScaleFactor
                color: UM.Theme.getColor('monitor_secondary_button_text')
                font: UM.Theme.getFont('medium')
                text: printer.activePrintJob.state === 'paused' ? catalog.i18nc('@action:button', 'Resume Print') : catalog.i18nc('@action:button', 'Pause Print')
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                height: 18 * screenScaleFactor
                renderType: Text.NativeRendering
            }
            implicitHeight: 32 * screenScaleFactor
            implicitWidth: 96 * screenScaleFactor
            visible: printer && printer.activePrintJob && (printer.activePrintJob.state === 'active' || printer.activePrintJob.state === 'paused')
            onClicked: base.enabled ? OutputDevice.pauseOrResumePrint() : {}
            enabled: true
        }

        Button {
            id: cancelPrintButton
            anchors {
                verticalCenter: parent.verticalCenter
                right: parent.right
                rightMargin: 18 * screenScaleFactor
            }
            background: Rectangle {
                color: UM.Theme.getColor('monitor_secondary_button_shadow')
                radius: 2 * screenScaleFactor
                Rectangle {
                    anchors.fill: parent
                    anchors.bottomMargin: 2 * screenScaleFactor
                    color: cancelPrintButton.hovered ? UM.Theme.getColor('monitor_secondary_button_hover') : UM.Theme.getColor('monitor_secondary_button')
                    radius: 2 * screenScaleFactor
                }
            }
            contentItem: Label {
                anchors.fill: parent
                anchors.bottomMargin: 2 * screenScaleFactor
                color: UM.Theme.getColor('monitor_secondary_button_text')
                font: UM.Theme.getFont('medium')
                text: catalog.i18nc('@action:button', 'Cancel Print')
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                height: 18 * screenScaleFactor
                renderType: Text.NativeRendering
            }
            implicitHeight: 32 * screenScaleFactor
            implicitWidth: 96 * screenScaleFactor
            visible: printer && printer.activePrintJob && (printer.activePrintJob.state === 'active' || printer.activePrintJob.state === 'paused')
            onClicked: base.enabled ? OutputDevice.cancelPrint() : {}
            enabled: true
        }

        Cura.SecondaryButton {
            id: printCachedButton
            anchors {
                verticalCenter: parent.verticalCenter
                right: parent.right
                rightMargin: 18 * screenScaleFactor
            }
            text: catalog.i18nc('@button', 'Print Cached Model')
            enabled: !OutputDevice.isUploading
            visible: printer && printer.activePrintJob && printer.activePrintJob.state === 'not_started'
            busy: OutputDevice.has_start_print_request_in_progress
            onClicked: base.enabled ? OutputDevice.startPrint() : {}
        }
    }
}
