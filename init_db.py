import sqlite3

def init_db():
    conn = sqlite3.connect('reservoir_dynamic.db')
    cursor = conn.cursor()
    
    # Create reservoir_data table
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
    
    conn.commit()
    conn.close()

    # Create reservoir_static.db and its table
    conn = sqlite3.connect('reservoir_static.db')
    cursor = conn.cursor()
    
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
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()