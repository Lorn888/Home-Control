import csv
import io
import pyodbc
import logging

def get_db_connection():
    try:
        connection_string = (
            "Driver={ODBC Driver 18 for SQL Server};"  
            "Server=tcp:myserver888.database.windows.net,1433;"  
            "Database=MyDb;" 
            "Uid=patryk888888;"  
            "Pwd=Limpiki1;"  
            "Encrypt=yes;"  
            "TrustServerCertificate=no;" 
            "Connection Timeout=30;" 
        )
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
  