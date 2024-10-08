import os
import re
import csv
import io
import logging
import pyodbc
import azure.functions as func
import time
from datetime import datetime

def get_db_connection_with_retries(max_retries=4, delay=5):
    for attempt in range(max_retries):
        try:
            # Fetch connection details from environment variables
            server = os.getenv('DB_SERVER')
            database = os.getenv('DB_NAME')
            username = os.getenv('DB_USERNAME')
            password = os.getenv('DB_PASSWORD')
            driver = '{ODBC Driver 18 for SQL Server}'
    
            # Use the correct connection string format for ODBC Driver 18
            connection_string = (
                f"Driver={driver};"
                f"Server=tcp:{server},1433;"
                f"Database={database};"
                f"Uid={username};"
                f"Pwd={password};"
                "Encrypt=yes;"
                "TrustServerCertificate=no;"
                "Connect Timeout=120;"
            )
            connection = pyodbc.connect(connection_string)
            return connection
        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed to connect: {e}")
            time.sleep(delay)
    logging.error(f"All {max_retries} attempts to connect to the database failed.")
    raise

def insert_data_with_retries(csv_data, max_retries=3, delay=5):
    for attempt in range(max_retries):
        try:
            connection = get_db_connection_with_retries()
            cursor = connection.cursor()
            
            # SQL query to insert data into your table
            sql_query = """
            INSERT INTO LightingData (Timestamp, DeviceName, State, Brightness)
            VALUES (?, ?, ?, ?)
            """
            
            # Use csv.DictReader to read the CSV data
            reader = csv.DictReader(io.StringIO(csv_data))
            for row in reader:
                # Handle conversion of Brightness to integer, default to None if not valid
                state = row['State']
                brightness = row['Brightness']
                
                # Apply conditions
                if state == '0':
                    state = 'off'
                else:
                    state = 'on'
                
                if state == 'on' and not brightness or brightness == 'N/A':
                    brightness = 254
                elif state == 'off' and not brightness or brightness == 'N/A':
                    brightness = 0
                else:
                    try:
                        brightness = int(brightness)
                    except ValueError:
                        brightness = 0  # or another default value

                # Convert Timestamp to datetime object
                timestamp = datetime.strptime(row['Timestamp'], '%d/%m/%Y, %H:%M:%S')

                cursor.execute(sql_query, timestamp, row['Device Name'], state, brightness)
            
            connection.commit()
            cursor.close()
            connection.close()
            return  # If successful, exit the function
        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed to insert data: {e}")
            time.sleep(delay)
    logging.error(f"All {max_retries} attempts to insert data failed.")
    raise

def remove_ansi_codes(text):
    logging.debug("Removing ANSI codes from text.")
    ansi_escape = re.compile(r'\x1b\[[-0-9;]*m')
    clean_text = ansi_escape.sub('', text)
    logging.debug("ANSI codes removed.")
    return clean_text

def main(myblob: func.InputStream, outputBlob: func.Out[bytes]):
    logging.info(f"Processing blob: {myblob.name} with size: {myblob.length} bytes")
    
    try:
        # Read the blob content
        try:
            logging.debug("Attempting to read blob content.")
            log_content = myblob.read().decode('utf-8')
            logging.info("Log content read successfully.")
        except Exception as e:
            logging.error(f"Error reading blob content: {e}")
            return  # Exit if reading the blob fails

        # Clean the log content
        clean_log = remove_ansi_codes(log_content)

        # Define device mapping
        device_mapping = {
            "0x0c4314fffe327b16": "Ceiling Light",
            "0xb4e3f9fffe8bb6e2": "Wardrobe Overhead Lights",
            "0xb4e3f9fffe923b0f": "Wardrobe Spotlight",
            "0x003c84fffe66d621": "Inside Wardrobe Lights",
            "0xb4e3f9fffe77d07b": "3D Printer Lights",
        }

        # Define log entry pattern
        log_entry_pattern = re.compile(
            r'\[(?P<Timestamp>\d{2}/\d{2}/\d{4}, \d{2}:\d{2}:\d{2})\] \[homebridge-z2m\] Publish to \'zigbee2mqtt/(?P<DeviceID>[0-9a-fx]+)/(set|get)\': \'(?P<Data>{.*})\''
        )

        # Find matches
        try:
            logging.debug("Finding matches in the log content.")
            matches = list(log_entry_pattern.finditer(clean_log))
            logging.info(f"Found {len(matches)} log entries.")
        except Exception as e:
            logging.error(f"Error finding matches in log content: {e}")
            return

        # Prepare output in CSV format
        try:
            logging.debug("Preparing CSV output.")
            output = io.StringIO()
            fieldnames = ['Timestamp', 'Device Name', 'State', 'Brightness']
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()

            for match in matches:
                timestamp = match.group('Timestamp')
                device_id = match.group('DeviceID')
                data = match.group('Data')

                device_name = device_mapping.get(device_id, device_id)  # Defaults to device_id if not found

                # Extract state and brightness with error handling
                state_match = re.search(r'"state":"(.*?)"', data) or re.search(r'"state":(\d)', data)
                state = state_match.group(1) if state_match else "Unknown"

                brightness_match = re.search(r'"brightness":(\d+)', data)
                brightness = brightness_match.group(1) if brightness_match else "N/A"

                writer.writerow({
                    'Timestamp': timestamp,
                    'Device Name': device_name, 
                    'State': state,
                    'Brightness': brightness
                })

            output.seek(0)
            processed_data = output.getvalue().encode('utf-8')  # Convert string to bytes
            logging.info("CSV data prepared successfully.")
        except Exception as e:
            logging.error(f"Error preparing CSV output: {e}")
            return

        # Set the processed data to the output blob
        try:
            logging.debug("Attempting to write processed data to output blob.")
            outputBlob.set(processed_data)
            logging.info("Processed data written to output blob.")
        except Exception as e:
            logging.error(f"Error writing to output blob: {e}")
            return

        # Insert data into the database
        try:
            logging.debug("Attempting to insert data into the database.")
            insert_data_with_retries(output.getvalue())  # Pass CSV data as a string to the insert_data_with_retries function
            logging.info("Data inserted into database.")
        except Exception as e:
            logging.error(f"Error inserting data into database: {e}")

    except Exception as e:
        logging.error(f"Unexpected error occurred: {e}")