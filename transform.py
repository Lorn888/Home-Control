import csv

def transform_logs_to_csv(log_file_path, csv_file_path):
    with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as log_file:
        log_lines = log_file.readlines()
    
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Timestamp', 'Log Level', 'Message'])  # Header row
        
        for line in log_lines:
            # Example of parsing logic; modify according to your log format
            parts = line.split(' ', 3)  # Split line into timestamp, log level, and message
            if len(parts) == 4:
                timestamp = parts[0] + ' ' + parts[1]
                log_level = parts[2]
                message = parts[3].strip()
                csv_writer.writerow([timestamp, log_level, message])

# Update paths as necessary
log_file_path = 'homebridge.log'
csv_file_path = 'path_to_your_output_csv_file.csv'



transform_logs_to_csv(log_file_path, csv_file_path)
