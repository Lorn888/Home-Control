# Open the file to read IP addresses
with open('ips.txt', 'r') as file:
    lines = file.readlines()

# Open a new file to write the cleaned IP addresses
with open('clean_ips.txt', 'w') as file:
    for line in lines:
        # Remove quotation marks and commas, and write the cleaned line
        cleaned_line = line.replace('"', '').replace(',', '').strip()
        file.write(cleaned_line + '\n')
