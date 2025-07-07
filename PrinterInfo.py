import re

class Printer:
    def __init__(self):
        self.printer_info = ""
        self.x_coordinate = 0.0
        self.y_coordinate = 0.0
        self.z_coordinate = 0.0
        self.E_coordinate = 0.0
        self.hotend_temperature = 0.0
        self.heatbed_temperature = 0.0
        self.hotend_target_temperature = 0.0
        self.heatbed_target_temperature = 0.0
        self.printer_status = "Idle"
        self.print_progress = 0
        self.elapsed_time = ""
        self.sd_card_ok = False
        self.sd_card_files = []
        self.fan_speed = 0
        self.buffer = ""
        self.last_sd_byte = -1  # for pause detection
        self.raw_buffer = []
    def update_printer_variables(self):
        in_file_list = False
        sd_files = []

        responses = self.buffer.split("\n")
        if responses[-1] != '':
            self.buffer = responses[-1]
            responses.pop()

        self.raw_buffer.extend(responses)
        for line in responses:
            line = line.strip()

            # Handle SD file list
            if in_file_list:
                if line == "End file list":
                    in_file_list = False
                    self.sd_card_files = sd_files
                elif line:
                    sd_files.append(line.strip())
                continue

            if line == "Begin file list":
                in_file_list = True
                sd_files = []
                self.sd_card_ok = True
                continue

            # Position parsing (M114)
            if "X:" in line and "Count" in line:
                line = line.split("Count")[0]  # Strip off "Count ..." part

            match = re.findall(r'([XYZE]):\s*(-?\d+\.?\d*)', line)
            for axis, value in match:
                if axis == 'X':
                    self.x_coordinate = float(value)
                elif axis == 'Y':
                    self.y_coordinate = float(value)
                elif axis == 'Z':
                    self.z_coordinate = float(value)
                elif axis == 'E':
                    self.E_coordinate = float(value)

            # Temperature parsing (M105)
            if 'T:' in line and 'B:' in line:
                t_match = re.search(r'T:([\d.]+)\s*/\s*([\d.]+)', line)
                b_match = re.search(r'B:([\d.]+)\s*/\s*([\d.]+)', line)
                if t_match:
                    self.hotend_temperature = float(t_match.group(1))
                    self.hotend_target_temperature = float(t_match.group(2))
                if b_match:
                    self.heatbed_temperature = float(b_match.group(1))
                    self.heatbed_target_temperature = float(b_match.group(2))

                fan_match = re.search(r'@:(\d+)', line)
                if fan_match:
                    self.fan_speed = int(fan_match.group(1))

            # SD card status
            if "SD card ok" in line:
                self.sd_card_ok = True
            elif "SD card error" in line:
                self.sd_card_ok = False

            # Print time
            if "Print time:" in line:
                parts = line.split("Print time:", 1)
                if len(parts) > 1:
                    self.elapsed_time = parts[1].strip()
            elif "Time:" in line:
                parts = line.split("Time:", 1)
                if len(parts) > 1:
                    self.elapsed_time = parts[1].strip()

            # Printer info
            if "Printer:" in line:
                parts = line.split("Printer:", 1)
                if len(parts) > 1:
                    self.printer_info = parts[1].strip()

            # M27 - SD printing byte
            if 'Not SD printing' in line:
                self.printer_status = 'Idle'
                self.print_progress = 0
                self.last_sd_byte = -1
            elif 'SD printing byte' in line:
                m = re.search(r'SD printing byte (\d+)/(\d+)', line)
                if m:
                    done = int(m.group(1))
                    total = int(m.group(2))
                    percent = round((done / total) * 100, 1)
                    if self.last_sd_byte == done:
                        self.printer_status = 'Paused'
                    else:
                        self.printer_status = 'Printing'
                    self.print_progress = percent
                    self.last_sd_byte = done
