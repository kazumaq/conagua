// app.js

// Global variables
let chart;
const defaultState = 'Jalisco';
const defaultReservoir = 'LDCJL'; // Lago de Chapala
let fullStartDate, fullEndDate;
let currentData;

// Initialize the application
function init() {
    console.log("Initializing application...");
    fetchStates();
}

// Fetch list of states
function fetchStates() {
    console.log("Fetching states...");
    fetch('/api/states')
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.json();
        })
        .then(states => {
            console.log("States retrieved:", states);
            populateSelect('stateSelect', states, defaultState);
            fetchReservoirs(defaultState);
        })
        .catch(error => {
            console.error('Error fetching states:', error);
            alert('Failed to fetch states. Please check the console for more information.');
        });
}

// Fetch reservoirs for a given state
function fetchReservoirs(state) {
    console.log(`Fetching reservoirs for state: ${state}`);
    fetch(`/api/reservoirs/${state}`)
        .then(response => response.json())
        .then(reservoirs => {
            console.log(`Retrieved ${reservoirs.length} reservoirs for ${state}`);
            populateSelect('reservoirSelect', reservoirs.map(r => ({ value: r.clavesih, text: `${r.nombrecomun} (${r.clavesih})` })), defaultReservoir);
            loadReservoirData(defaultReservoir);
        })
        .catch(error => {
            console.error('Error fetching reservoirs:', error);
        });
}

// Load and display reservoir data
function loadReservoirData(clavesih) {
    console.log(`Loading data for reservoir: ${clavesih}`);
    fetch(`/api/data/${clavesih}`)
        .then(response => response.json())
        .then(data => {
            console.log(`Retrieved ${data.length} data points for reservoir ${clavesih}`);
            currentData = data;
            processReservoirData(data);
        })
        .catch(error => {
            console.error('Error loading reservoir data:', error);
        });
}

// Process and display reservoir data
function processReservoirData(data) {
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

// Update the chart with new data
function updateChart(data) {
    console.log(`Updating chart with ${data.length} data points`);
    const dates = data.map(d => d.fechamonitoreo);
    const volumes = data.map(d => d.almacenaactual);
    const percentages = data.map(d => d.llenano * 100);

    if (chart) {
        chart.destroy();
    }

    const ctx = document.getElementById('reservoirChart').getContext('2d');
    if (!ctx) {
        console.error("Canvas context not found");
        return;
    }

    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [
                {
                    label: 'Volume (hm³)',
                    data: volumes,
                    borderColor: 'rgb(75, 192, 192)',
                    yAxisID: 'y-axis-1',
                },
                {
                    label: 'Percentage (%)',
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
                        text: 'Volume (hm³)'
                    }
                },
                'y-axis-2': {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Percentage (%)'
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
    console.log("Chart updated successfully");
}

// Display latest data
function displayLatestData(data) {
    console.log(`Displaying latest data: ${JSON.stringify(data)}`);
    const latestDataDiv = document.getElementById('latestData');
    if (!latestDataDiv) {
        console.error("latestData element not found in the DOM");
        return;
    }
    latestDataDiv.innerHTML = `
        <h3>Latest Data (${data.fechamonitoreo})</h3>
        <p>Current Volume: ${data.almacenaactual.toFixed(2)} hm³</p>
        <p>Percentage Full: ${(data.llenano * 100).toFixed(2)}%</p>
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
        console.error("No current data available");
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

    // Initialize the application
    init();
});