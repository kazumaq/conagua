const LAKE_CHAPALA_ID = 'LDCJL';
const RESERVOIR_IDS = [
    'SBBMX', 'PIRMX', 'TEPMC', 'PFBMX', 'TMUMC', 'SLSGJ', 'TPTMX', 'VGRTP',
    'PNLGJ', 'IALGJ', 'COIMC', 'LDYGJ', 'PRSGJ', 'EPLGJ', 'GLNGJ', 'MABGJ',
    'LDFMC', 'POLJL', 'UREMC', 'DGNMC', 'GUAMC', 'JARMC', 'CPAMC'
];

let chart;
let currentLanguage = 'en';

const translations = {
    en: {
        title: "Lerma-Chapala Basin Visualization",
        language: "Language",
        startDate: "Start Date",
        endDate: "End Date",
        updateGraph: "Update Graph",
        reservoirData: "Reservoir Data",
        reservoirName: "Reservoir Name",
        currentVolume: "Current Volume (hm³)",
        percentageFull: "Percentage Full",
        lakeChapalaVolume: "Lake Chapala Volume",
        otherReservoirsVolume: "Other Reservoirs Volume",
        lakeChapalaHistoricalAverage: "Lake Chapala Historical Average",
        date: "Date",
        volume: "Volume (hm³)"
    },
    es: {
        title: "Visualización de la Cuenca Lerma-Chapala",
        language: "Idioma",
        startDate: "Fecha de Inicio",
        endDate: "Fecha de Fin",
        updateGraph: "Actualizar Gráfico",
        reservoirData: "Datos de Embalses",
        reservoirName: "Nombre del Embalse",
        currentVolume: "Volumen Actual (hm³)",
        percentageFull: "Porcentaje Lleno",
        lakeChapalaVolume: "Volumen del Lago de Chapala",
        otherReservoirsVolume: "Volumen de Otros Embalses",
        lakeChapalaHistoricalAverage: "Promedio Histórico del Lago de Chapala",
        date: "Fecha",
        volume: "Volumen (hm³)"
    }
};

function changeLanguage(lang) {
    currentLanguage = lang;
    document.querySelectorAll('[data-translate]').forEach(element => {
        const key = element.getAttribute('data-translate');
        element.textContent = translations[lang][key];
    });
    if (chart) {
        updateChartLanguage();
    }
}

async function fetchData(startDate, endDate) {
    const reservoirData = await Promise.all(RESERVOIR_IDS.map(id => 
        fetch(`/api/data/${id}?start_date=${startDate}&end_date=${endDate}`).then(res => res.json())
    ));
    const lakeData = await fetch(`/api/data/${LAKE_CHAPALA_ID}?start_date=${startDate}&end_date=${endDate}`).then(res => res.json());

    return { reservoirData, lakeData };
}

function processData(reservoirData, lakeData) {
    const dates = lakeData.map(d => new Date(d.fechamonitoreo));
    const lakeVolume = lakeData.map(d => d.almacenaactual);
    const reservoirVolume = dates.map((date, index) => {
        return reservoirData.reduce((sum, reservoir) => {
            const dayData = reservoir.find(d => d.fechamonitoreo === lakeData[index].fechamonitoreo);
            return sum + (dayData ? dayData.almacenaactual : 0);
        }, 0);
    });

    // Calculate historical average (simplified - using all available data)
    const historicalAverage = lakeVolume.reduce((sum, vol) => sum + vol, 0) / lakeVolume.length;

    return { dates, lakeVolume, reservoirVolume, historicalAverage };
}

function createOrUpdateChart(data) {
    const ctx = document.getElementById('graph').getContext('2d');

    const chartData = {
        labels: data.dates,
        datasets: [
            {
                label: translations[currentLanguage].lakeChapalaVolume,
                data: data.lakeVolume,
                borderColor: 'blue',
                fill: false,
                borderWidth: 1,
                pointRadius: 0
            },
            {
                label: translations[currentLanguage].otherReservoirsVolume,
                data: data.reservoirVolume,
                borderColor: 'green',
                fill: false,
                borderWidth: 1,
                pointRadius: 0
            },
            {
                label: translations[currentLanguage].lakeChapalaHistoricalAverage,
                data: Array(data.dates.length).fill(data.historicalAverage),
                borderColor: 'red',
                borderDash: [5, 5],
                fill: false,
                borderWidth: 1,
                pointRadius: 0
            }
        ]
    };

    if (chart) {
        chart.data = chartData;
        chart.options.scales.x.title.text = translations[currentLanguage].date;
        chart.options.scales.y.title.text = translations[currentLanguage].volume;
        chart.update();
    } else {
        chart = new Chart(ctx, {
            type: 'line',
            data: chartData,
            options: {
                responsive: true,
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'day'
                        },
                        title: {
                            display: true,
                            text: translations[currentLanguage].date
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: translations[currentLanguage].volume
                        }
                    }
                }
            }
        });
    }
}

function updateChartLanguage() {
    chart.data.datasets[0].label = translations[currentLanguage].lakeChapalaVolume;
    chart.data.datasets[1].label = translations[currentLanguage].otherReservoirsVolume;
    chart.data.datasets[2].label = translations[currentLanguage].lakeChapalaHistoricalAverage;
    chart.options.scales.x.title.text = translations[currentLanguage].date;
    chart.options.scales.y.title.text = translations[currentLanguage].volume;
    chart.update();
}

function createReservoirTable(reservoirData, lakeData) {
    const tableBody = document.getElementById('reservoir-table-body');
    tableBody.innerHTML = ''; // Clear existing rows

    // Add Lake Chapala
    const lakeLatest = lakeData[lakeData.length - 1];
    const lakeRow = createTableRow(lakeLatest);
    tableBody.appendChild(lakeRow);

    // Add other reservoirs
    reservoirData.forEach(reservoir => {
        if (reservoir.length > 0) {
            const latestData = reservoir[reservoir.length - 1];
            const row = createTableRow(latestData);
            tableBody.appendChild(row);
        }
    });
}

function createTableRow(data) {
    const row = document.createElement('tr');
    row.innerHTML = `
        <td>${data.nombrecomun}</td>
        <td>${data.almacenaactual.toFixed(2)}</td>
        <td>${data.fill_percentage.toFixed(2)}%</td>
    `;
    return row;
}

async function updateGraph() {
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;

    if (!startDate || !endDate) {
        alert(currentLanguage === 'en' ? 'Please select both start and end dates.' : 'Por favor, seleccione ambas fechas de inicio y fin.');
        return;
    }

    try {
        const { reservoirData, lakeData } = await fetchData(startDate, endDate);
        const processedData = processData(reservoirData, lakeData);
        createOrUpdateChart(processedData);
        createReservoirTable(reservoirData, lakeData);
    } catch (error) {
        console.error('Error updating graph:', error);
        alert(currentLanguage === 'en' ? 'Failed to update graph. Please try again.' : 'Error al actualizar el gráfico. Por favor, inténtelo de nuevo.');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const updateButton = document.getElementById('update-graph');
    updateButton.addEventListener('click', updateGraph);

    const languageSelect = document.getElementById('languageSelect');
    languageSelect.addEventListener('change', (e) => changeLanguage(e.target.value));

    // Set initial date range (e.g., last month)
    const endDate = new Date();
    const startDate = new Date();
    startDate.setMonth(startDate.getMonth() - 1);

    document.getElementById('start-date').value = startDate.toISOString().split('T')[0];
    document.getElementById('end-date').value = endDate.toISOString().split('T')[0];

    changeLanguage(currentLanguage);
    updateGraph();
});
