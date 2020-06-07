// Copyright 2020 Luc Rubio <luc@loociano.com>
// Plugin is licensed under the GNU Lesser General Public License v3.0.
import QtQuick 2.2
import QtQuick.Controls 2.0
import UM 1.3 as UM
import Cura 1.5 as Cura

Item {
    id: extruder
    property var hotendTemperature : null // int
    property var targetHotendTemperature : null // int
    property int max_hotend_temperature : OutputDevice.max_hotend_temperature
    property var historical_hotend_temperatures : OutputDevice.historical_hotend_temperatures // Array[int]
    property int num_chart_points : OutputDevice.num_chart_points
    height: 40 * screenScaleFactor
    width: childrenRect.width

    function generateLabels() {
        console.info('generate labels');
        var result = [];
        for (var i = 0; i < extruder.num_chart_points; i++) {
            result.push('');
        }
        return result;
    }

    function generateData() {
        if (chart) {
            chart.animateToNewData();
        }
        return extruder.historical_hotend_temperatures
    }

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
        width: 36 * screenScaleFactor
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
        width: childrenRect.width
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
            enabled: !OutputDevice.isUploading && !OutputDevice.has_target_hotend_in_progress
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

    Chart {
        id: chart
        anchors {
            right: parent.right
            top: parent.top
        }
        width: 140 * screenScaleFactor
        height: 40 * screenScaleFactor
        chartType: 'line'
        chartData: {
            return {
                labels: extruder.generateLabels(),
                datasets: [
                    {
                        fill: false,
                        pointRadius: 0,
                        borderColor: 'rgba(128,192,255,255)',
                        borderWidth: 3,
                        hoverBorderWidth: 0,
                        hoverRadius: 0,
                        hitRadius: 0,
                        data: extruder.generateData(),
                    }
                ]
            }
        }
        chartOptions: {
            return {
                animation: false,
                maintainAspectRatio: false,
                responsive: true,
                legend: {
                    display: false,
                },
                tooltips: {
                    enabled: false,
                },
                scales: {
                    xAxes: [{
                        display: false,
                        position: 'bottom',
                    }],
                    yAxes: [{
                        type: 'linear',
                        display: true,
                        position: 'right',
                        ticks: {
                            max: 260,
                            min: 0,
                            maxTicksLimit: 2
                        }
                    }]
                }
            }
        }
    }
}
