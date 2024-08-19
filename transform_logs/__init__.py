import re
import csv
import io
import logging
import azure.functions as func
from database import insert_log, create_table

def remove_ansi_codes(text):
    ansi_escape = re.compile(r'\x1b\[[-0-9;]*m')
    return ansi_escape.sub('', text)

def main(myblob: func.InputStream, outputBlob: func.Out[bytes]):
    logging.info(f"Processing blob: {myblob.name} with size: {myblob.length} bytes")
    
    try:
        # Read the blob content
        log_content = myblob.read().decode('utf-8')
        logging.info("Log content read successfully.")

        # Clean the log content
        clean_log = remove_ansi_codes(log_content)
        logging.info("ANSI codes removed from log content.")

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
        matches = list(log_entry_pattern.finditer(clean_log))
        logging.info(f"Found {len(matches)} log entries.")

        # Prepare output in CSV format
        output = io.StringIO()
        fieldnames = ['Timestamp', 'Device Name', 'State', 'Brightness']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for match in matches:
            timestamp = match.group('Timestamp')
            device_id = match.group('DeviceID')
            data = match.group('Data')

            device_name = device_mapping.get(device_id, device_id)  # Defaults to device_id if not found

            try:
                state = re.search(r'"state":"(.*?)"', data).group(1)
            except AttributeError:
                state = re.search(r'"state":(\d)', data).group(1)

            try:
                brightness = re.search(r'"brightness":(\d+)', data).group(1)
            except AttributeError:
                brightness = None

            writer.writerow({
                'Timestamp': timestamp,
                'Device Name': device_name, 
                'State': state,
                'Brightness': brightness
            })

            # Insert data into the database
            insert_log(timestamp, device_name, state, brightness)

        output.seek(0)
        processed_data = output.getvalue().encode('utf-8')  # Convert string to bytes

        # Set the processed data to the output blob
        outputBlob.set(processed_data)
        logging.info("Processed data written to output blob.")

    except Exception as e:
        logging.error(f"Error occurred: {e}")
