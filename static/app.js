document.addEventListener('DOMContentLoaded', function() {
  const stateSelect = document.getElementById('state-select');
  const reservoirSelect = document.getElementById('reservoir-select');
  const dateRange = document.getElementById('date-range');
  const plotDiv = document.getElementById('plot');

  // Fetch states and populate the state dropdown
  fetch('/api/states')
      .then(response => response.json())
      .then(states => {
          states.forEach(state => {
              const option = document.createElement('option');
              option.value = state;
              option.textContent = state;
              stateSelect.appendChild(option);
          });
      });

  // Event listener for state selection
  stateSelect.addEventListener('change', function() {
      const state = this.value;
      reservoirSelect.innerHTML = '<option value="">Select a reservoir</option>';
      reservoirSelect.disabled = !state;

      if (state) {
          fetch(`/api/reservoirs/${state}`)
              .then(response => response.json())
              .then(reservoirs => {
                  reservoirs.forEach(reservoir => {
                      const option = document.createElement('option');
                      option.value = reservoir.clavesih;
                      option.textContent = reservoir.nombrecomun;
                      reservoirSelect.appendChild(option);
                  });
              });
      }
  });

  // Event listener for reservoir selection and date range
  reservoirSelect.addEventListener('change', updatePlot);
  dateRange.addEventListener('change', updatePlot);

  function updatePlot() {
      const clavesih = reservoirSelect.value;
      const [startDate, endDate] = dateRange.value.split(',');

      if (clavesih && startDate && endDate) {
          fetch(`/api/data/${clavesih}?start_date=${startDate}&end_date=${endDate}`)
              .then(response => response.json())
              .then(data => {
                  const traces = [{
                      x: data.map(d => d.fechamonitoreo),
                      y: data.map(d => d.almacenaactual),
                      type: 'scatter',
                      mode: 'lines+markers',
                      name: 'Water Storage'
                  }];

                  const layout = {
                      title: 'Water Storage Over Time',
                      xaxis: { title: 'Date' },
                      yaxis: { title: 'Storage (Million m³)' }
                  };

                  Plotly.newPlot(plotDiv, traces, layout);
              });
      }
  }
});