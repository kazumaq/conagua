import json
import sqlite3
import os
from datetime import datetime
import sys

def create_and_fill_databases(input_directory):
    try:
        # Connect to the databases
        static_conn = sqlite3.connect('reservoir_static.db')
        dynamic_conn = sqlite3.connect('reservoir_dynamic.db')

        static_cursor = static_conn.cursor()
        dynamic_cursor = dynamic_conn.cursor()

        # Create tables
        create_static_table(static_cursor)
        create_dynamic_table(dynamic_cursor)

        # Process JSON files
        json_files = [f for f in os.listdir(input_directory) if f.endswith('.json')]
        if not json_files:
            raise ValueError(f"No JSON files found in {input_directory}")

        latest_file = max(json_files, key=lambda x: os.path.getmtime(os.path.join(input_directory, x)))

        # Insert static data from the latest file
        process_static_data(os.path.join(input_directory, latest_file), static_cursor)

        # Process all files for dynamic data
        for filename in json_files:
            process_dynamic_data(os.path.join(input_directory, filename), dynamic_cursor)

        # Commit changes and close connections
        static_conn.commit()
        dynamic_conn.commit()
        static_conn.close()
        dynamic_conn.close()

        print("Databases created and filled successfully.")

    except sqlite3.Error as e:
        print(f"SQLite error occurred: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

def create_static_table(cursor):
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reservoirs (
        clavesih TEXT PRIMARY KEY,
        nombreoficial TEXT,
        nombrecomun TEXT,
        estado TEXT,
        nommunicipio TEXT,
        regioncna TEXT,
        latitud REAL,
        longitud REAL,
        uso TEXT,
        corriente TEXT,
        tipovertedor TEXT,
        inicioop TEXT,
        elevcorona TEXT,
        bordolibre REAL,
        nameelev REAL,
        namealmac REAL,
        namoelev REAL,
        namoalmac REAL,
        alturacortina TEXT
    )
    ''')

def create_dynamic_table(cursor):
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reservoir_data (
        idmonitoreodiario INTEGER PRIMARY KEY,
        clavesih TEXT,
        fechamonitoreo DATE,
        elevacionactual REAL,
        almacenaactual REAL,
        FOREIGN KEY (clavesih) REFERENCES reservoirs(clavesih)
    )
    ''')

def process_static_data(file_path, cursor):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        if not data:
            raise ValueError(f"No data found in {file_path}")

        for item in data:
            cursor.execute('''
            INSERT OR REPLACE INTO reservoirs 
            (clavesih, nombreoficial, nombrecomun, estado, nommunicipio, regioncna, 
            latitud, longitud, uso, corriente, tipovertedor, inicioop, elevcorona, 
            bordolibre, nameelev, namealmac, namoelev, namoalmac, alturacortina)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item['clavesih'],
                item['nombreoficial'],
                item['nombrecomun'],
                item['estado'],
                item['nommunicipio'],
                item['regioncna'],
                item['latitud'],
                item['longitud'],
                item['uso'],
                item['corriente'],
                item['tipovertedor'],
                item['inicioop'],
                item['elevcorona'],
                item['bordolibre'],
                item['nameelev'],
                item['namealmac'],
                item['namoelev'],
                item['namoalmac'],
                item['alturacortina']
            ))

    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file {file_path}")
        raise
    except KeyError as e:
        print(f"Error: Missing key {e} in file {file_path}")
        raise
    except Exception as e:
        print(f"Error processing static data from {file_path}: {e}")
        raise

def process_dynamic_data(file_path, cursor):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        for item in data:
            cursor.execute('''
            INSERT OR REPLACE INTO reservoir_data 
            (idmonitoreodiario, clavesih, fechamonitoreo, elevacionactual, almacenaactual)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                item['idmonitoreodiario'],
                item['clavesih'],
                datetime.strptime(item['fechamonitoreo'], '%Y-%m-%d').date(),
                item['elevacionactual'],
                item['almacenaactual']
            ))
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file {file_path}")
        raise
    except KeyError as e:
        print(f"Error: Missing key {e} in file {file_path}")
        raise
    except ValueError as e:
        print(f"Error: Invalid date format in file {file_path}: {e}")
        raise
    except Exception as e:
        print(f"Error processing dynamic data from {file_path}: {e}")
        raise

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python preprocessor.py <path_to_data_directory>")
        sys.exit(1)
    
    input_directory = sys.argv[1]
    if not os.path.isdir(input_directory):
        print(f"Error: {input_directory} is not a valid directory")
        sys.exit(1)

    create_and_fill_databases(input_directory)