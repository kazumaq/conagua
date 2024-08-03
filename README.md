<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Water Reservoir Visualization</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .controls {
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            justify-content: center;
        }
        select, input, button {
            padding: 5px;
            font-size: 16px;
        }
        #reservoirChart {
            width: 100%;
            max-width: 800px;
            height: 400px;
        }
        #latestData {
            margin-top: 20px;
            text-align: center;
        }
    </style>
</head>
<body>
    <h1>Water Reservoir Visualization</h1>
    
    <div class="controls">
        <select id="stateSelect"></select>
        <select id="reservoirSelect"></select>
        <input type="date" id="startDate">
        <input type="date" id="endDate">
        <button id="updateButton">Update</button>
    </div>

    <canvas id="reservoirChart"></canvas>
    
    <div id="latestData"></div>

    <script src="/static/app.js"></script>
</body>
</html>