import csv
import io
import pyodbc
import logging

def get_db_connection():
    try:
        # Replace these with your actual connection details
        server = 'myserver888.database.windows.net'
        database = 'MyDb'
        username = 'patryk888888'
        password = 'Limpiki1'
        driver = '{ODBC Driver 17 for SQL Server}'

        connection_string = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        connection = pyodbc.connect(connection_string)
        return connection
    except Exception as e:
        logging.error(f"Error connecting to the database: {e}")
        raise

def insert_data(csv_data):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # SQL query to insert data into your table
        sql_query = """
        INSERT INTO LightingData (Timestamp, DeviceName, State, Brightness)
        VALUES (?, ?, ?, ?)
        """
        
        # Use csv.DictReader to read the CSV data
        reader = csv.DictReader(io.StringIO(csv_data))
        for row in reader:
            cursor.execute(sql_query, row['Timestamp'], row['Device Name'], row['State'], row['Brightness'])
        
        connection.commit()
        cursor.close()
        connection.close()
    except Exception as e:
        logging.error(f"Error inserting data into the database: {e}")
        raise
