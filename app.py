from flask import Flask, jsonify, send_from_directory, render_template, request
import sqlite3
from datetime import datetime, timedelta
import os
import logging

app = Flask(__name__, static_folder='static', template_folder='templates')
logging.basicConfig(level=logging.DEBUG)

def get_db_connection(db_name):
    try:
        conn = sqlite3.connect(db_name)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        app.logger.error(f"Database connection error: {e}")
        return None

@app.route('/')
def main_page():
    return send_from_directory('static_pages', 'index.html')

@app.route('/embalses')
def embalses_main():
    return send_from_directory('static_pages', 'embalses_main.html')

@app.route('/embalses/niveles')
def embalses_niveles():
    # Your existing code for showing reservoir levels
    return render_template('embalses_niveles.html')

@app.route('/embalses/simulacion')
def embalses_simulacion():
    # This function will handle the logic for your simulation page
    return render_template('embalses_simulacion.html')

@app.route('/embalses/simulacion2')
def embalses_simulacion2():
    # This function will handle the logic for your simulation page
    return render_template('embalses_simulacion2.html')

@app.route('/api/states')
def get_states():
    try:
        conn = get_db_connection('reservoir_static.db')
        if conn is None:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT estado FROM reservoirs ORDER BY estado')
        states = [row['estado'] for row in cursor.fetchall()]
        conn.close()
        
        app.logger.info(f"Retrieved {len(states)} states")
        return jsonify(states)
    except Exception as e:
        app.logger.error(f"Error in get_states: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/reservoirs/<state>')
def get_reservoirs(state):
    try:
        conn = get_db_connection('reservoir_static.db')
        if conn is None:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        cursor.execute('SELECT clavesih, nombrecomun FROM reservoirs WHERE estado = ? ORDER BY nombrecomun', (state,))
        reservoirs = [{'clavesih': row['clavesih'], 'nombrecomun': row['nombrecomun']} for row in cursor.fetchall()]
        conn.close()
        
        app.logger.info(f"Retrieved {len(reservoirs)} reservoirs for state {state}")
        return jsonify(reservoirs)
    except Exception as e:
        app.logger.error(f"Error in get_reservoirs: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/reservoir/<clavesih>')
def get_reservoir_info(clavesih):
    conn = get_db_connection('reservoir_static.db')
    reservoir = conn.execute('SELECT * FROM reservoirs WHERE clavesih = ?', (clavesih,)).fetchone()
    conn.close()
    if reservoir is None:
        return jsonify({'error': 'Reservoir not found'}), 404
    return jsonify(dict(reservoir))

def calculate_fill_percentage(almacenaactual, namoalmac):
    if namoalmac == 0:
        return 0  # Avoid division by zero
    return (almacenaactual / namoalmac) * 100

@app.route('/api/data/<clavesih>')
def get_reservoir_data(clavesih):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Connect to both databases
    dynamic_conn = get_db_connection('reservoir_dynamic.db')
    static_conn = get_db_connection('reservoir_static.db')

    # Query dynamic data
    dynamic_query = '''
        SELECT * FROM reservoir_data 
        WHERE clavesih = ? AND fechamonitoreo BETWEEN ? AND ? 
        ORDER BY fechamonitoreo
    '''
    dynamic_data = dynamic_conn.execute(dynamic_query, (clavesih, start_date, end_date)).fetchall()

    # Query static data
    static_query = 'SELECT * FROM reservoirs WHERE clavesih = ?'
    static_data = static_conn.execute(static_query, (clavesih,)).fetchone()

    # Close connections
    dynamic_conn.close()
    static_conn.close()

    # Combine dynamic and static data
    result = []
    for row in dynamic_data:
        data_point = dict(row)
        if static_data:
            data_point.update(dict(static_data))
            # Calculate fill percentage
            data_point['fill_percentage'] = calculate_fill_percentage(data_point['almacenaactual'], data_point['namoalmac'])
        result.append(data_point)

    app.logger.info(f"Retrieved {len(result)} data points for reservoir {clavesih}")
    if result:
        app.logger.debug(f"Date range: {result[0]['fechamonitoreo']} to {result[-1]['fechamonitoreo']}")

    return jsonify(result)

@app.route('/api/latest/<clavesih>')
def get_latest_data(clavesih):
    dynamic_conn = get_db_connection('reservoir_dynamic.db')
    static_conn = get_db_connection('reservoir_static.db')

    latest = dynamic_conn.execute('''
        SELECT * FROM reservoir_data 
        WHERE clavesih = ?
        ORDER BY fechamonitoreo DESC
        LIMIT 1
    ''', (clavesih,)).fetchone()

    static_data = static_conn.execute('SELECT * FROM reservoirs WHERE clavesih = ?', (clavesih,)).fetchone()

    dynamic_conn.close()
    static_conn.close()

    if latest is None:
        return jsonify({'error': 'No data found for this reservoir'}), 404
    
    result = dict(latest)
    if static_data:
        result.update(dict(static_data))
        # Calculate fill percentage
        result['fill_percentage'] = calculate_fill_percentage(result['almacenaactual'], result['namoalmac'])
    
    app.logger.info(f"Latest data for reservoir {clavesih}: {result}")
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

