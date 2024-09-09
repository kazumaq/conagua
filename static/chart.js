let chart;

export function createOrUpdateChart(data, translations, currentLanguage) {
    const ctx = document.getElementById('reservoirChart');
    if (!ctx) {
        console.error("Canvas element 'reservoirChart' not found");
        return;
    }

    const dates = data.map(d => d.fechamonitoreo);
    const volumes = data.map(d => d.almacenaactual);
    const percentages = data.map(d => d.fill_percentage);

    // Calculate the range for the percentage axis
    const maxPercentage = Math.max(...percentages);
    const minPercentage = Math.min(...percentages);
    const percentageBuffer = (maxPercentage - minPercentage) * 0.1; // 10% buffer

    // Determine the y-axis-2 (percentage) range
    const yAxis2Min = Math.max(0, minPercentage - percentageBuffer);
    const yAxis2Max = maxPercentage + percentageBuffer;

    if (chart) {
        chart.data.labels = dates;
        chart.data.datasets[0].data = volumes;
        chart.data.datasets[1].data = percentages;

        // Update the percentage axis range
        chart.options.scales['y-axis-2'].min = yAxis2Min;
        chart.options.scales['y-axis-2'].max = yAxis2Max;

        chart.update();
    } else {
        chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: `${translations[currentLanguage].volume} (${translations[currentLanguage].cubicHectometers})`,
                        data: volumes,
                        borderColor: 'rgb(75, 192, 192)',
                        yAxisID: 'y-axis-1',
                    },
                    {
                        label: `${translations[currentLanguage].percentage} (%)`,
                        data: percentages,
                        borderColor: 'rgb(255, 99, 132)',
                        yAxisID: 'y-axis-2',
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'month'
                        }
                    },
                    'y-axis-1': {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: `${translations[currentLanguage].volume} (${translations[currentLanguage].cubicHectometers})`
                        }
                    },
                    'y-axis-2': {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: `${translations[currentLanguage].percentage} (%)`
                        },
                        min: yAxis2Min,
                        max: yAxis2Max,
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
    }
    console.log("Chart created or updated successfully");
}

export function updateChartLanguage(translations, currentLanguage) {
    if (chart) {
        chart.data.datasets[0].label = `${translations[currentLanguage].volume} (${translations[currentLanguage].cubicHectometers})`;
        chart.data.datasets[1].label = `${translations[currentLanguage].percentage} (%)`;
        chart.options.scales['y-axis-1'].title.text = `${translations[currentLanguage].volume} (${translations[currentLanguage].cubicHectometers})`;
        chart.options.scales['y-axis-2'].title.text = `${translations[currentLanguage].percentage} (%)`;
        chart.update();
    }
}
