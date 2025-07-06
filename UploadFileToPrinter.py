import time

from mdns import printers
from PrinterToBackend import  send_commandd_to_printer


def calculate_checksum(line):
    cs = 0
    for c in line:
        cs ^= ord(c)
    return cs

def format_gcode_line(line, line_number):
    line = line.strip()
    if not line or line.startswith(';'):
        return None

    # Remove comment part
    line_no_comment = line.split(';')[0].strip()

    # Format with line number and checksum
    gcode = f'N{line_number} {line_no_comment}'
    checksum = calculate_checksum(gcode)
    return f'{gcode}*{checksum}'


def send_chunk(printer_ip,chunk):
    payload = {"commands": [chunk]}
    # print(payload)
    send_commandd_to_printer(printer_ip,chunk)
    time.sleep(0.001)


# Send header

def upload_file_to_printer(printer_ip, data):
    max_len = 45 * 1024  # chunk size in characters
    file_name = data.get('file_name')
    file_name = file_name[:8] + ".gco"
    file_path = data.get('file_path')
    priority = data.get('priority')



    header = ['M110 N0', 'M21', f'M28 {file_name}']
    footer = ['M29']

    send_chunk(printer_ip,header)

    # Process file with line numbers and checksums
    with open(file_path, 'r') as f:
        curr_chunk = []
        curr_len = 13
        line_number = 1
        for line in f:
            formatted = format_gcode_line(line, line_number)
            if formatted:
                curr_chunk.append(formatted)
                curr_len += len(formatted) + 3
                line_number += 1

                if curr_len >= max_len:
                    try:
                        send_chunk(curr_chunk)
                    except ConnectionResetError:
                        print('Connection error')
                    curr_chunk = []
                    curr_len = 0

        if curr_chunk:
            try:
                send_chunk(curr_chunk)
            except ConnectionResetError:
                pass
    send_chunk(footer)