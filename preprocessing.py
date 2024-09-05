import json
import sqlite3
import os
from datetime import datetime
import sys

from logger_config import setup_logging

logger = setup_logging(__name__)

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

        logger.info(f"Found {len(json_files)} JSON files")
        
        # Sort files by date in the filename
        sorted_files = sorted(json_files, key=lambda x: x.split('.')[0])
        logger.info(f"Files will be processed in this order: {sorted_files}")

        latest_file = sorted_files[-1]
        logger.info(f"Latest file: {latest_file}")

        # Insert static data from the latest file
        process_static_data(os.path.join(input_directory, latest_file), static_cursor)

        # Process all files for dynamic data
        for filename in sorted_files:
            process_dynamic_data(os.path.join(input_directory, filename), dynamic_cursor)

        # Commit changes and close connections
        static_conn.commit()
        dynamic_conn.commit()
        static_conn.close()
        dynamic_conn.close()

        logging.info("Databases created and filled successfully.")

    except sqlite3.Error as e:
        logging.error(f"SQLite error occurred: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
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
    logging.info("Static table created or already exists")

def create_dynamic_table(cursor):
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reservoir_data (
        clavesih TEXT,
        fechamonitoreo DATE,
        elevacionactual REAL,
        almacenaactual REAL,
        PRIMARY KEY (clavesih, fechamonitoreo),
        FOREIGN KEY (clavesih) REFERENCES reservoirs(clavesih)
    )
    ''')
    logging.info("Dynamic table created or already exists")

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
        logging.info(f"Processed static data from {file_path}")

    except json.JSONDecodeError:
        logging.error(f"Error: Invalid JSON in file {file_path}")
        raise
    except KeyError as e:
        logging.error(f"Error: Missing key {e} in file {file_path}")
        raise
    except Exception as e:
        logging.error(f"Error processing static data from {file_path}: {e}")
        raise

def process_dynamic_data(file_path, cursor):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        logging.info(f"Processing file: {file_path}")
        logging.info(f"Total records in file: {len(data)}")
        
        chapala_data = []
        for item in data:
            if item['clavesih'] == 'LDCJL':
                chapala_data.append(item)
            cursor.execute('''
            INSERT OR REPLACE INTO reservoir_data 
            (clavesih, fechamonitoreo, elevacionactual, almacenaactual)
            VALUES (?, ?, ?, ?)
            ''', (
                item['clavesih'],
                datetime.strptime(item['fechamonitoreo'], '%Y-%m-%d').date(),
                item['elevacionactual'],
                item['almacenaactual']
            ))
        
        logging.info(f"Inserted or updated {len(data)} records from {file_path}")
        
        if chapala_data:
            logging.info(f"Lago de Chapala data in {file_path}:")
            for item in chapala_data:
                logging.info(f"Date: {item['fechamonitoreo']}, Elevation: {item['elevacionactual']}, Storage: {item['almacenaactual']}")
        else:
            logging.warning(f"No Lago de Chapala data found in {file_path}")

    except json.JSONDecodeError:
        logging.error(f"Error: Invalid JSON in file {file_path}")
        raise
    except KeyError as e:
        logging.error(f"Error: Missing key {e} in file {file_path}")
        raise
    except ValueError as e:
        logging.error(f"Error: Invalid date format in file {file_path}: {e}")
        raise
    except Exception as e:
        logging.error(f"Error processing dynamic data from {file_path}: {e}")
        raise

def verify_database_contents():
    try:
        conn = sqlite3.connect('reservoir_dynamic.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM reservoir_data")
        total_records = cursor.fetchone()[0]
        logging.info(f"Total records in reservoir_data: {total_records}")

        cursor.execute("SELECT COUNT(*) FROM reservoir_data WHERE clavesih = 'LDCJL'")
        chapala_records = cursor.fetchone()[0]
        logging.info(f"Total records for Lago de Chapala: {chapala_records}")

        cursor.execute("SELECT fechamonitoreo, elevacionactual, almacenaactual FROM reservoir_data WHERE clavesih = 'LDCJL' ORDER BY fechamonitoreo DESC LIMIT 10")
        latest_chapala_data = cursor.fetchall()
        logging.info("Latest 10 records for Lago de Chapala:")
        for record in latest_chapala_data:
            logging.info(f"Date: {record[0]}, Elevation: {record[1]}, Storage: {record[2]}")

        conn.close()
    except sqlite3.Error as e:
        logging.error(f"Error verifying database contents: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python preprocessor.py <path_to_data_directory>")
        sys.exit(1)
    
    input_directory = sys.argv[1]
    if not os.path.isdir(input_directory):
        logging.error(f"Error: {input_directory} is not a valid directory")
        sys.exit(1)

    create_and_fill_databases(input_directory)
    verify_database_contents()
