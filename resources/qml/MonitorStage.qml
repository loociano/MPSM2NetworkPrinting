// Copyright 2020 Luc Rubio <luc@loociano.com>
// Plugin is licensed under the GNU Lesser General Public License v3.0.
import QtQuick 2.2
import QtQuick.Controls 2.0
import UM 1.3 as UM
import Cura 1.0 as Cura

Component
{
    Rectangle
    {
        height: maximumHeight
        width: maximumWidth
        color: UM.Theme.getColor('monitor_stage_background')
        Component.onCompleted: forceActiveFocus()

        UM.I18nCatalog {
            id: catalog
            name: 'cura'
        }

        Item {
            anchors {
                top: parent.top
                topMargin: 48 * screenScaleFactor
            }
            width: parent.width
            height: 264 * screenScaleFactor

            Item {
                height: centerSection.height
                width: maximumWidth
            
                Item {
                    id: centerSection
                    anchors {
                        verticalCenter: parent.verticalCenter
                        horizontalCenter: parent.horizontalCenter
                    }
                    width: 834 * screenScaleFactor
                    height: printerCard.height
                    z: 1

                    Column {
                        MonitorPrinterCard {
                            id: printerCard
                            printer: OutputDevice.printer
                        }

                        Item {
                            anchors {
                                top: printerCard.bottom
                                topMargin: UM.Theme.getSize('default_margin').height
                                right: printerCard.right
                            }
                            height: UM.Theme.getSize("monitor_text_line").height
                            width: childrenRect.width

                            Image {
                                id: externalLinkIcon
                                anchors {
                                    right: linkLabel.left
                                    verticalCenter: parent.verticalCenter
                                }
                                width: 16 * screenScaleFactor
                                height: 16 * screenScaleFactor
                                source: UM.Theme.getIcon('external_link')
                            }
                            Label {
                                id: linkLabel
                                anchors {
                                    right: parent.right
                                    verticalCenter: externalLinkIcon.verticalCenter
                                }
                                color: UM.Theme.getColor('monitor_text_link')
                                font: UM.Theme.getFont('default')
                                linkColor: UM.Theme.getColor('monitor_text_link')
                                text: catalog.i18nc('@label link to bug tracker', 'Report an issue')
                                renderType: Text.NativeRendering
                            }
                            MouseArea {
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: Qt.openUrlExternally('https://github.com/loociano/MPSM2NetworkPrinting/issues')
                                onEntered: linkLabel.font.underline = true
                                onExited: linkLabel.font.underline = false
                            }
                        }
                    }
                }
            }
        }
    }
}
