import { createOrUpdateChart, updateChartLanguage } from './chart.js';

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

// Fetch list of states
function fetchStates() {
    console.log("Fetching states...");
    return fetch('/api/states')
        .then(response => {
            console.log("Received response from /api/states:", response);
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

function updateURL(state, reservoir, startDate, endDate) {
    const params = new URLSearchParams({
        state: state,
        reservoir: reservoir,
        startDate: startDate,
        endDate: endDate
    });
    const newURL = `https://${window.location.hostname}${window.location.pathname}?${params.toString()}`;
    console.log('Updating URL to:', newURL);
    try {
        window.history.replaceState({}, '', newURL);
        console.log('URL updated successfully');
    } catch (error) {
        console.error('Error updating URL:', error);
    }
}

// Function to change language
function changeLanguage(lang) {
    currentLanguage = lang;
    document.querySelectorAll('[data-translate]').forEach(element => {
        const key = element.getAttribute('data-translate');
        element.textContent = translations[lang][key];
    });
    if (chart) {
        updateChartLanguage(translations, currentLanguage);
    }
    if (currentData) {
        displayLatestData(currentData[currentData.length - 1]);
    }
    // Update placeholders and labels for date inputs
    document.getElementById('startDate').placeholder = translations[lang].startDate;
    document.getElementById('endDate').placeholder = translations[lang].endDate;
}

// Initialize the application
function init() {
    console.log("Initializing application...");
    
    // Get URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const stateParam = urlParams.get('state');
    const reservoirParam = urlParams.get('reservoir');
    const startDateParam = urlParams.get('startDate');
    const endDateParam = urlParams.get('endDate');

    // Set date inputs
    const endDate = endDateParam ? new Date(endDateParam) : new Date();
    const startDate = startDateParam ? new Date(startDateParam) : new Date(endDate.getFullYear(), endDate.getMonth() - 1, endDate.getDate());
    
    document.getElementById('startDate').value = formatDate(startDate);
    document.getElementById('endDate').value = formatDate(endDate);

    fetchStates()
        .then(defaultState => {
            const stateToUse = stateParam || defaultState;
            document.getElementById('stateSelect').value = stateToUse;
            return fetchReservoirs(stateToUse);
        })
        .then(reservoirs => {
            if (reservoirParam) {
                document.getElementById('reservoirSelect').value = reservoirParam;
                return loadReservoirData(reservoirParam);
            } else if (!stateParam && !reservoirParam) {
                // If no parameters are provided, default to Lake Chapala
                document.getElementById('stateSelect').value = 'Jalisco';
                return fetchReservoirs('Jalisco').then(() => {
                    document.getElementById('reservoirSelect').value = 'LDCJL';
                    return loadReservoirData('LDCJL');
                });
            } else if (reservoirs && reservoirs.length > 0) {
                document.getElementById('reservoirSelect').value = reservoirs[0].clavesih;
                return loadReservoirData(reservoirs[0].clavesih);
            }
        })
        .catch(error => {
            console.error('Error initializing application:', error);
            displayErrorMessage(error);
        });

    document.getElementById('languageSelect').addEventListener('change', (e) => changeLanguage(e.target.value));
}

// Fetch reservoirs for a given state
function fetchReservoirs(state) {
    console.log(`Fetching reservoirs for state: ${state}`);
    return fetch(`/api/reservoirs/${state}`)
        .then(response => {
            console.log(`Received response from /api/reservoirs/${state}:`, response);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.json();
        })
        .then(reservoirs => {
            console.log(`Retrieved ${reservoirs.length} reservoirs for ${state}:`, reservoirs);
            populateSelect('reservoirSelect', reservoirs.map(r => ({ value: r.clavesih, text: `${r.nombrecomun} (${r.clavesih})` })), null);
            
            // Clear the current chart
            clearChart();
            
            // Enable the reservoir select
            document.getElementById('reservoirSelect').disabled = false;
            
            return reservoirs;
        })
        .catch(error => {
            console.error(`Error fetching reservoirs for state ${state}:`, error);
            alert(translations[currentLanguage].errorFetchingReservoirs);
            throw error;
        });
}

// Clear the current chart
function clearChart() {
    const chartContainer = document.getElementById('reservoirChart');
    chartContainer.innerHTML = '<p>Please select a reservoir</p>';
    const latestDataDiv = document.getElementById('latestData');
    latestDataDiv.innerHTML = '';
}

// Load and display reservoir data
function loadReservoirData(clavesih) {
    console.log(`Loading data for reservoir: ${clavesih}`);

    const startDate = '1991-01-01';
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
                console.log(`First data point: ${JSON.stringify(data[0])}`);
                console.log(`Last data point: ${JSON.stringify(data[data.length - 1])}`);
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

    // Set default range to last month
    let defaultStartDate = new Date(fullEndDate);
    defaultStartDate.setMonth(defaultStartDate.getMonth() - 1);
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
    console.log(`Full date range available: ${formatDate(fullStartDate)} to ${formatDate(fullEndDate)}`);

    updateChart(data.filter(d => new Date(d.fechamonitoreo) >= defaultStartDate));
    displayLatestData(data[data.length - 1]);
}

// Create or update the chart
function updateChart(data) {
    console.log(`Updating chart with ${data.length} data points`);
    createOrUpdateChart(data, translations, currentLanguage);
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
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    const state = document.getElementById('stateSelect').value;
    const reservoir = document.getElementById('reservoirSelect').value;
    
    updateURL(state, reservoir, startDate, endDate);
    
    if (currentData) {
        const filteredData = currentData.filter(d => {
            const date = new Date(d.fechamonitoreo);
            return date >= new Date(startDate) && date <= new Date(endDate);
        });
        console.log(`Filtered ${filteredData.length} data points`);
        updateChart(filteredData);
    } else {
        console.error(translations[currentLanguage].noCurrentData);
        displayErrorMessage(new Error(translations[currentLanguage].noCurrentData));
    }
}

function displayErrorMessage(error) {
    const chartContainer = document.getElementById('reservoirChart');
    chartContainer.innerHTML = `<p>Error: ${error.message}</p>`;
    const latestDataDiv = document.getElementById('latestData');
    latestDataDiv.innerHTML = '<p>Error loading latest data.</p>';
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM fully loaded and parsed");
    
    document.getElementById('stateSelect').addEventListener('change', (e) => {
        fetchReservoirs(e.target.value).then(() => {
            // Clear the current chart when state changes
            clearChart();
        });
    });

    document.getElementById('reservoirSelect').addEventListener('change', (e) => {
        if (e.target.value) {
            loadReservoirData(e.target.value);
            updateURL(document.getElementById('stateSelect').value, e.target.value, document.getElementById('startDate').value, document.getElementById('endDate').value);
        }
    });

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
