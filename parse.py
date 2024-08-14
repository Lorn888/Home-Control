import re
import csv

def remove_ansi_codes(text):
    ansi_escape = re.compile(r'\x1b\[[-0-9;]*m')
    return ansi_escape.sub('', text)

with open('lights.log', 'r') as file:
    log_content = file.read()

clean_log = remove_ansi_codes(log_content)

device_mapping = {
    "0x0c4314fffe327b16": "Ceiling Light",
    "0xb4e3f9fffe8bb6e2": "Wardrobe Overhead Lights",
    "0xb4e3f9fffe923b0f": "Wardrobe Spotlight",
    "0x003c84fffe66d621": "Inside Wardrobe Lights",
    "0xb4e3f9fffe77d07b": "3D Printer Lights",
}

log_entry_pattern = re.compile(
    r'\[(?P<Timestamp>\d{2}/\d{2}/\d{4}, \d{2}:\d{2}:\d{2})\] \[homebridge-z2m\] Publish to \'zigbee2mqtt/(?P<DeviceID>[0-9a-fx]+)/(set|get)\': \'(?P<Data>{.*})\''
)

matches = log_entry_pattern.finditer(clean_log)

with open('lights_parsed.csv', 'w', newline='') as csvfile:
    fieldnames = ['Timestamp', 'Device Name', 'State', 'Brightness']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

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

print("Data has been written to lights_parsed.csv")
