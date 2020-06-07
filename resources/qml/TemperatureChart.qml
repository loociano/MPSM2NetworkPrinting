// Copyright 2020 Luc Rubio <luc@loociano.com>
// Plugin is licensed under the GNU Lesser General Public License v3.0.
import QtQuick 2.3
import "../js/Chart.js" as Chart

Chart {
    id: root

    property var temperatures // Array[number]
    property int targetTemperature

    function generateFlatData(value) {
        var result = [];
        for (var i = 0; i < temperatures.length; i++) {
            result.push(value);
        }
        return result;
    }

    function generateData() {
        if (root) {
            root.animateToNewData();
        }
        return root.temperatures
    }

    chartType: 'line'
    chartData: {
        return {
            labels: root.generateFlatData(''),
            datasets: [{
                fill: false,
                pointRadius: 0,
                borderColor: 'rgba(128,192,255,255)',
                borderWidth: 2,
                hoverBorderWidth: 0,
                hoverRadius: 0,
                hitRadius: 0,
                data: root.generateData(),
            },{
                fill: false,
                pointRadius: 0,
                borderColor: 'rgba(4,100,185,255)',
                borderWidth: 1,
                borderDash: [100, 100],
                hitRadius: 0,
                data: root.generateFlatData(root.targetTemperature),
            }]
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