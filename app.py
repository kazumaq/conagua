from flask import Flask, jsonify, send_from_directory, request
import sqlite3
from datetime import datetime
import os

app = Flask(__name__, static_folder='static')

def get_db_connection(db_name):
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/states')
def get_states():
    conn = get_db_connection('reservoir_static.db')
    states = conn.execute('SELECT DISTINCT estado FROM reservoirs').fetchall()
    conn.close()
    return jsonify([state['estado'] for state in states])

@app.route('/api/reservoirs/<state>')
def get_reservoirs(state):
    conn = get_db_connection('reservoir_static.db')
    reservoirs = conn.execute('SELECT clavesih, nombrecomun FROM reservoirs WHERE estado = ?', (state,)).fetchall()
    conn.close()
    return jsonify([{'clavesih': res['clavesih'], 'nombrecomun': res['nombrecomun']} for res in reservoirs])

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
    start_date = request.args.get('start_date', '1900-01-01')
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))

    conn = get_db_connection('reservoir_dynamic.db')
    data = conn.execute('''
        SELECT * FROM reservoir_data 
        WHERE clavesih = ? AND fechamonitoreo BETWEEN ? AND ?
        ORDER BY fechamonitoreo
    ''', (clavesih, start_date, end_date)).fetchall()
    conn.close()

    return jsonify([dict(row) for row in data])

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
    return jsonify(dict(latest))

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)