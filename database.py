import psycopg2
from psycopg2 import sql
import os

# Get connection details from environment variables
connection_params = {
    "dbname": os.getenv("dbname"),
    "user": os.getenv("user"),
    "password": os.getenv("password"),
    "host": os.getenv("host"),
    "port": os.getenv("port", 5432)
}

def get_connection():
    return psycopg2.connect(**connection_params)

def create_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql.SQL('''
        CREATE TABLE IF NOT EXISTS Logs (
            Timestamp TIMESTAMP,
            DeviceName VARCHAR(100),
            State VARCHAR(50),
            Brightness INT
        )
    '''))
    conn.commit()
    cursor.close()
    conn.close()

def insert_log(timestamp, device_name, state, brightness):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql.SQL('''
        INSERT INTO Logs (Timestamp, DeviceName, State, Brightness)
        VALUES (%s, %s, %s, %s)
    '''), (timestamp, device_name, state, brightness))
    conn.commit()
    cursor.close()
    conn.close()
