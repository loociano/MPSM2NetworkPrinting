// Copyright 2020 Luc Rubio <luc@loociano.com>
// Plugin is licensed under the GNU Lesser General Public License v3.0.
import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.3 as UM
import Cura 1.0 as Cura
import QtGraphicalEffects 1.0

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

                            UM.RecolorImage {
                                id: externalLinkIcon
                                anchors {
                                    right: linkLabel.left
                                    rightMargin: UM.Theme.getSize('narrow_margin').width
                                    verticalCenter: parent.verticalCenter
                                }
                                color: UM.Theme.getColor('monitor_text_link')
                                source: UM.Theme.getIcon('external_link')
                                width: UM.Theme.getSize('monitor_external_link_icon').width * 0.8
                                height: UM.Theme.getSize('monitor_external_link_icon').height * 0.8
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
                                onClicked: Qt.openUrlExternally('http://loociano.com/mpsm2-cura-plugin')
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
