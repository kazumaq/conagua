import os
from flask import Flask, jsonify, send_from_directory, render_template, request, abort
import sqlite3
import logging
from datetime import datetime, timedelta

app = Flask(__name__, static_folder='static', template_folder='templates')
logging.basicConfig(level=logging.DEBUG)

# Use environment variables for configuration
app.config['DATABASE'] = os.environ.get('DATABASE_URL', 'sqlite:///reservoir_dynamic.db')

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
    state = request.args.get('state', default=None, type=str)
    reservoir = request.args.get('reservoir', default=None, type=str)
    start_date = request.args.get('startDate', default=None, type=str)
    end_date = request.args.get('endDate', default=None, type=str)
    
    # Validate state
    if state:
        conn = get_db_connection('reservoir_static.db')
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT estado FROM reservoirs WHERE estado = ?', (state,))
        if not cursor.fetchone():
            state = None
        conn.close()
    
    # Validate reservoir
    if reservoir:
        conn = get_db_connection('reservoir_static.db')
        cursor = conn.cursor()
        cursor.execute('SELECT clavesih FROM reservoirs WHERE clavesih = ?', (reservoir,))
        if not cursor.fetchone():
            reservoir = None
        conn.close()
    
    # Validate dates
    try:
        if start_date:
            datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        start_date = None
        end_date = None
    
    return render_template('embalses_niveles.html', 
                           state=state, 
                           reservoir=reservoir, 
                           start_date=start_date, 
                           end_date=end_date)

@app.route('/embalses/simulacion')
def embalses_simulacion():
    return render_template('embalses_simulacion.html')

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

    # Validate dates
    try:
        if start_date:
            datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

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
