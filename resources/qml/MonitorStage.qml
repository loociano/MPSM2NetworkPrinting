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

                    MonitorPrinterCard {
                        id: printerCard
                        printer: {
                            return OutputDevice.printer
                        }
                    }
                }
            }
        }
    }
}
