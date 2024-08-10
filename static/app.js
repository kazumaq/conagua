// app.js

// Global variables
let chart;
const defaultState = 'Jalisco';
const defaultReservoir = 'LDCJL'; // Lago de Chapala
let fullStartDate, fullEndDate;
let currentData;

// Translations
const translations = {
    en: {
        title: "Water Reservoir Visualization",
        fullRange: "Show Full Range",
        latestData: "Latest Data",
        currentVolume: "Current Volume",
        percentageFull: "Percentage Full",
        volume: "Volume",
        percentage: "Percentage",
        cubicHectometers: "hm³",
        startDate: "Start Date",
        endDate: "End Date",
        errorFetchingStates: "Failed to fetch states. Please check the console for more information.",
        errorFetchingReservoirs: "Error fetching reservoirs",
        errorLoadingReservoirData: "Error loading reservoir data",
        noCurrentData: "No current data available",
        latestDataElementNotFound: "latestData element not found in the DOM",
        language: "Language",
        state: "State",
        reservoir: "Reservoir"
    },
    es: {
        title: "Visualización de Embalses de Agua",
        fullRange: "Mostrar Rango Completo",
        latestData: "Datos más Recientes",
        currentVolume: "Volumen Actual",
        percentageFull: "Porcentaje Lleno",
        volume: "Volumen",
        percentage: "Porcentaje",
        cubicHectometers: "hm³",
        startDate: "Fecha de Inicio",
        endDate: "Fecha de Fin",
        errorFetchingStates: "Error al obtener estados. Por favor, revise la consola para más información.",
        errorFetchingReservoirs: "Error al obtener embalses",
        errorLoadingReservoirData: "Error al cargar datos del embalse",
        noCurrentData: "No hay datos actuales disponibles",
        latestDataElementNotFound: "Elemento latestData no encontrado en el DOM",
        language: "Idioma",
        state: "Estado",
        reservoir: "Embalse"
    }
};

let currentLanguage = 'en';

// Function to change language
function changeLanguage(lang) {
    currentLanguage = lang;
    document.querySelectorAll('[data-translate]').forEach(element => {
        const key = element.getAttribute('data-translate');
        element.textContent = translations[lang][key];
    });
    if (chart) {
        updateChartLanguage();
    }
    if (currentData) {
        displayLatestData(currentData[currentData.length - 1]);
    }
    // Update placeholders and labels for date inputs
    document.getElementById('startDate').placeholder = translations[lang].startDate;
    document.getElementById('endDate').placeholder = translations[lang].endDate;
}

// Function to update chart language
function updateChartLanguage() {
    if (chart) {
        chart.data.datasets[0].label = `${translations[currentLanguage].volume} (${translations[currentLanguage].cubicHectometers})`;
        chart.data.datasets[1].label = `${translations[currentLanguage].percentage} (%)`;
        chart.options.scales['y-axis-1'].title.text = `${translations[currentLanguage].volume} (${translations[currentLanguage].cubicHectometers})`;
        chart.options.scales['y-axis-2'].title.text = `${translations[currentLanguage].percentage} (%)`;
        chart.update();
    }
}

// Fetch list of states
function fetchStates() {
    console.log("Fetching states...");
    return fetch('/api/states')
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.json();
        })
        .then(states => {
            console.log("States retrieved:", states);
            populateSelect('stateSelect', states, defaultState);
            return defaultState;
        })
        .catch(error => {
            console.error('Error fetching states:', error);
            alert(translations[currentLanguage].errorFetchingStates);
            throw error;
        });
}

// Initialize the application
function init() {
    console.log("Initializing application...");
    // Set default dates
    const endDate = new Date();
    const startDate = new Date();
    startDate.setMonth(startDate.getMonth() - 1);
    
    document.getElementById('startDate').value = formatDate(startDate);
    document.getElementById('endDate').value = formatDate(endDate);

    fetchStates()
        .then(fetchReservoirs)
        .then(loadReservoirData)
        .catch(error => {
            console.error('Error initializing application:', error);
        });

    document.getElementById('languageSelect').addEventListener('change', (e) => changeLanguage(e.target.value));
}

// Fetch reservoirs for a given state
function fetchReservoirs(state) {
    console.log(`Fetching reservoirs for state: ${state}`);
    return fetch(`/api/reservoirs/${state}`)
        .then(response => response.json())
        .then(reservoirs => {
            console.log(`Retrieved ${reservoirs.length} reservoirs for ${state}`);
            populateSelect('reservoirSelect', reservoirs.map(r => ({ value: r.clavesih, text: `${r.nombrecomun} (${r.clavesih})` })), defaultReservoir);
            
            // Check if the default reservoir exists
            const reservoirSelect = document.getElementById('reservoirSelect');
            const defaultReservoirOption = Array.from(reservoirSelect.options).find(option => option.value === defaultReservoir);
            if (!defaultReservoirOption) {
                console.warn(`Default reservoir ${defaultReservoir} not found in the list. Using the first available reservoir.`);
                defaultReservoir = reservoirSelect.options[0].value;
            }
            
            return defaultReservoir;
        })
        .catch(error => {
            console.error(translations[currentLanguage].errorFetchingReservoirs, error);
            throw error;
        });
}

// Load and display reservoir data
function loadReservoirData(clavesih) {
    console.log(`Loading data for reservoir: ${clavesih}`);
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    console.log(`Date range: ${startDate} to ${endDate}`);

    // Add a small delay to ensure DOM is updated
    setTimeout(() => {
        fetch(`/api/data/${clavesih}?start_date=${startDate}&end_date=${endDate}`)
            .then(response => {
                console.log(`Response status: ${response.status}`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log(`Retrieved ${data.length} data points for reservoir ${clavesih}`);
                if (data.length === 0) {
                    console.warn(`No data received for reservoir ${clavesih}`);
                    displayNoDataMessage();
                    return;
                }
                currentData = data;
                processReservoirData(data);
            })
            .catch(error => {
                console.error(`Error loading data for reservoir ${clavesih}:`, error);
                displayErrorMessage(error);
            });
    }, 100);
}

function displayNoDataMessage() {
    const chartContainer = document.getElementById('reservoirChart');
    chartContainer.innerHTML = '<p>No data available for the selected date range.</p>';
    const latestDataDiv = document.getElementById('latestData');
    latestDataDiv.innerHTML = '<p>No current data available.</p>';
}

function displayErrorMessage(error) {
    const chartContainer = document.getElementById('reservoirChart');
    chartContainer.innerHTML = `<p>Error loading data: ${error.message}</p>`;
    const latestDataDiv = document.getElementById('latestData');
    latestDataDiv.innerHTML = '<p>Error loading latest data.</p>';
}

// Process and display reservoir data
function processReservoirData(data) {
    if (!data || data.length === 0) {
        console.warn("No data to process");
        return;
    }

    // Sort data by date
    data.sort((a, b) => new Date(a.fechamonitoreo) - new Date(b.fechamonitoreo));

    // Set full date range
    fullStartDate = new Date(data[0].fechamonitoreo);
    fullEndDate = new Date(data[data.length - 1].fechamonitoreo);

    console.log(`Full date range: ${fullStartDate.toISOString()} to ${fullEndDate.toISOString()}`);

    // Set default range to last year or full range if less than a year of data
    let defaultStartDate = new Date(fullEndDate);
    defaultStartDate.setFullYear(defaultStartDate.getFullYear() - 1);
    if (defaultStartDate < fullStartDate) defaultStartDate = fullStartDate;

    // Update date range inputs
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');

    startDateInput.value = formatDate(defaultStartDate);
    endDateInput.value = formatDate(fullEndDate);

    // Set min and max for date inputs
    startDateInput.min = formatDate(fullStartDate);
    startDateInput.max = formatDate(fullEndDate);
    endDateInput.min = formatDate(fullStartDate);
    endDateInput.max = formatDate(fullEndDate);

    console.log(`Date inputs set: start=${startDateInput.value}, end=${endDateInput.value}`);

    updateChart(data.filter(d => new Date(d.fechamonitoreo) >= defaultStartDate));
    displayLatestData(data[data.length - 1]);
}

// Create or update the chart
function createOrUpdateChart(data) {
    const ctx = document.getElementById('reservoirChart');
    if (!ctx) {
        console.error("Canvas element 'reservoirChart' not found");
        return;
    }

    const dates = data.map(d => d.fechamonitoreo);
    const volumes = data.map(d => d.almacenaactual);
    const percentages = data.map(d => d.fill_percentage);

    if (chart) {
        chart.data.labels = dates;
        chart.data.datasets[0].data = volumes;
        chart.data.datasets[1].data = percentages;
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
                        min: 0,
                        max: Math.max(100, Math.ceil(Math.max(...percentages))),
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

// Update the chart with new data
function updateChart(data) {
    console.log(`Updating chart with ${data.length} data points`);
    createOrUpdateChart(data);
}

// Display latest data
function displayLatestData(data) {
    console.log(`Displaying latest data: ${JSON.stringify(data)}`);
    const latestDataDiv = document.getElementById('latestData');
    if (!latestDataDiv) {
        console.error(translations[currentLanguage].latestDataElementNotFound);
        return;
    }
    latestDataDiv.innerHTML = `
        <h3>${translations[currentLanguage].latestData} (${data.fechamonitoreo})</h3>
        <p>${translations[currentLanguage].currentVolume}: ${data.almacenaactual.toFixed(2)} ${translations[currentLanguage].cubicHectometers}</p>
        <p>${translations[currentLanguage].percentageFull}: ${(data.fill_percentage).toFixed(2)}%</p>
    `;
}

// Utility function to format dates
function formatDate(date) {
    return date.toISOString().split('T')[0];
}

// Utility function to populate select elements
function populateSelect(selectId, options, defaultValue) {
    const select = document.getElementById(selectId);
    if (!select) {
        console.error(`${selectId} element not found in the DOM`);
        return;
    }
    select.innerHTML = ''; // Clear existing options
    options.forEach(option => {
        const optionElement = document.createElement('option');
        optionElement.value = option.value || option;
        optionElement.textContent = option.text || option;
        select.appendChild(optionElement);
    });
    select.value = defaultValue;
    console.log(`Populated ${selectId} with ${options.length} options, default value: ${defaultValue}`);
}

// Function to update data based on date range
function updateDataRange() {
    const startDate = new Date(document.getElementById('startDate').value);
    const endDate = new Date(document.getElementById('endDate').value);

    console.log(`Updating data range: ${startDate.toISOString()} to ${endDate.toISOString()}`);

    if (currentData) {
        const filteredData = currentData.filter(d => {
            const date = new Date(d.fechamonitoreo);
            return date >= startDate && date <= endDate;
        });
        console.log(`Filtered ${filteredData.length} data points`);
        updateChart(filteredData);
    } else {
        console.error(translations[currentLanguage].noCurrentData);
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM fully loaded and parsed");
    
    document.getElementById('stateSelect').addEventListener('change', (e) => fetchReservoirs(e.target.value));
    document.getElementById('reservoirSelect').addEventListener('change', (e) => loadReservoirData(e.target.value));
    document.getElementById('startDate').addEventListener('change', updateDataRange);
    document.getElementById('endDate').addEventListener('change', updateDataRange);
    
    document.getElementById('fullRangeButton').addEventListener('click', () => {
        document.getElementById('startDate').value = formatDate(fullStartDate);
        document.getElementById('endDate').value = formatDate(fullEndDate);
        updateDataRange();
    });

    // Set initial placeholders for date inputs
    document.getElementById('startDate').placeholder = translations[currentLanguage].startDate;
    document.getElementById('endDate').placeholder = translations[currentLanguage].endDate;

    // Initialize the application
    init();
});

// -------------------------
