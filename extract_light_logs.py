input_file = 'homebridge.log'
output_file = 'lights.log'

# Open the log file and the output file with UTF-8 encoding
with open(input_file, 'r', encoding='utf-8', errors='ignore') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
    for line in infile:
        # Check if the line contains 'zigbee2mqtt'
        if 'Publish to' in line:
            outfile.write(line)