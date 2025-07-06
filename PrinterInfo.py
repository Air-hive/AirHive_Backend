import re

import PrinterToBackend
#Printer Variables
class Printer():
    printer_info = None
    x_coordinate = 0.0
    y_coordinate = 0.0
    z_coordinate = 0.0
    E_coordinate = 0.0
    hotend_temperature = 0.0
    heatbed_temperature = 0.0
    hotend_target_temperature = 0.0
    heatbed_target_temperature = 0.0
    printer_status = None
    print_progress = None
    print_time = None
    sd_card_ok = None
    sd_card_files = []
    fan_speed = 0
    buffer = ''

    def update_printer_variables(self):
        global printer_info, x_coordinate, y_coordinate, z_coordinate, E_coordinate, \
            hotend_temperature, heatbed_temperature, hotend_target_temperature, heatbed_target_temperature, \
            printer_status, print_progress, print_time, sd_card_ok, sd_card_files, fan_speed, buffer

        in_file_list = False

        responses = buffer.split("\n")
        if responses[-1] != '':
            buffer = responses[-1]
            responses.pop()

        for line in responses:
            line = line.strip()

            # Handle SD card file list parsing
            if in_file_list:
                if line == "End file list":
                    in_file_list = False
                elif line:  # Skip empty lines
                    sd_card_files.append(line)
                continue

            # Check for special markers
            if line == "Begin file list":
                sd_card_files = []
                in_file_list = True
                continue

            # Parse key-value pairs
            tokens = line.split()
            for token in tokens:
                # Coordinates parsing
                if token.startswith('X:'):
                    try:
                        x_coordinate = float(token[2:])
                    except:
                        pass
                elif token.startswith('Y:'):
                    try:
                        y_coordinate = float(token[2:])
                    except:
                        pass
                elif token.startswith('Z:'):
                    try:
                        z_coordinate = float(token[2:])
                    except:
                        pass
                elif token.startswith('E:'):
                    try:
                        E_coordinate = float(token[2:])
                    except:
                        pass

                # Temperature parsing
                elif token.startswith('T:'):
                    try:
                        parts = token[2:].split('/')
                        hotend_temperature = float(parts[0])
                        if len(parts) > 1:
                            hotend_target_temperature = float(parts[1])
                    except:
                        pass
                elif token.startswith('B:'):
                    try:
                        parts = token[2:].split('/')
                        heatbed_temperature = float(parts[0])
                        if len(parts) > 1:
                            heatbed_target_temperature = float(parts[1])
                    except:
                        pass

                # Fan speed parsing
                elif token.startswith('F:') or token.startswith('Fan:'):
                    try:
                        value = token.split(':')[1]
                        fan_speed = int(re.search(r'\d+', value).group())
                    except:
                        pass

            # SD card status detection
            if "SD card ok" in line:
                sd_card_ok = True
            elif "SD card error" in line:
                sd_card_ok = False

            # Print progress detection
            if 'Progress:' in line or '%' in line:
                match = re.search(r'(\d{1,3}%)', line)
                if match:
                    print_progress = match.group(1)

            # Print time detection
            if "Print time:" in line:
                parts = line.split('Print time:', 1)
                if len(parts) > 1:
                    print_time = parts[1].strip()
            elif "Time:" in line:
                parts = line.split('Time:', 1)
                if len(parts) > 1:
                    print_time = parts[1].strip()

            # Printer info detection
            if "Printer:" in line:
                parts = line.split('Printer:', 1)
                if len(parts) > 1:
                    printer_info = parts[1].strip()

            # Printer status detection
            if "status:" in line:
                parts = line.split('status:', 1)
                if len(parts) > 1:
                    printer_status = parts[1].strip()
