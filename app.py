from flask import Flask, jsonify, send_from_directory, request
import sqlite3
from datetime import datetime, timedelta
import os
import logging

app = Flask(__name__, static_folder='static')
logging.basicConfig(level=logging.DEBUG)

def get_db_connection(db_name):
    try:
        conn = sqlite3.connect(db_name)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        app.logger.error(f"Database connection error: {e}")
        return None

@app.route('/embalses/niveles')
def index():
    return send_from_directory(app.static_folder, 'embalses_main.html')

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

@app.route('/api/data/<clavesih>')
def get_reservoir_data(clavesih):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    conn = get_db_connection('reservoir_dynamic.db')
    query = 'SELECT * FROM reservoir_data WHERE clavesih = ? ORDER BY fechamonitoreo'
    params = [clavesih]

    if start_date and end_date:
        query += ' AND fechamonitoreo BETWEEN ? AND ?'
        params.extend([start_date, end_date])

    data = conn.execute(query, params).fetchall()
    conn.close()

    result = [dict(row) for row in data]
    app.logger.info(f"Retrieved {len(result)} data points for reservoir {clavesih}")
    if result:
        app.logger.debug(f"Date range: {result[0]['fechamonitoreo']} to {result[-1]['fechamonitoreo']}")

    return jsonify(result)

@app.route('/api/latest/<clavesih>')
def get_latest_data(clavesih):
    conn = get_db_connection('reservoir_dynamic.db')
    latest = conn.execute('''
        SELECT * FROM reservoir_data 
        WHERE clavesih = ?
        ORDER BY fechamonitoreo DESC
        LIMIT 1
    ''', (clavesih,)).fetchone()
    conn.close()

    if latest is None:
        return jsonify({'error': 'No data found for this reservoir'}), 404
    
    result = dict(latest)
    app.logger.info(f"Latest data for reservoir {clavesih}: {result}")
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)