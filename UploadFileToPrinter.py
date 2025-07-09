import time
from fileinput import filename

from mdns import printers
from PrinterToBackend import  send_commandd_to_printer


def calculate_checksum(line):
    cs = 0
    for c in line:
        cs ^= ord(c)
    return cs

def format_gcode_line(line, line_number):
    try:
        line = line.strip()
        if not line or line.startswith(';'):
            return None

        # Remove comment part
        line_no_comment = line.split(';')[0].strip()
        # Format with line number and checksum
        gcode = f'N{line_number} {line_no_comment}'
        checksum = calculate_checksum(gcode)
        # print("line ",gcode, checksum)
        return f'{gcode}*{checksum}'
    except Exception as e:
        print("error formatting", e)

def send_chunk(printer_ip,chunk):
    response , status = send_commandd_to_printer(printer_ip,chunk)
    time.sleep(0.001)
    return status == 200

# Send header
def send_chunk(printer_ip, chunk):
    try:
        response, status = send_commandd_to_printer(printer_ip, chunk)

        if status != 200:
            print(f"[ERROR] HTTP {status}: {response}")
            return False

        if isinstance(response, dict) and response.get("error"):
            print(f"[ERROR] Printer responded with error: {response['error']}")
            return False

        return True
    except Exception as e:
        print(f"[EXCEPTION] Failed to send chunk: {e}")
        return False

def upload_file_to_printer(printer_ip, file_name, file_path):
    max_len = 45 * 1024  # chunk size in characters
    file_name = file_name.split('.')[0][:8] + ".gco"

    header = ['M110 N0', f'M28 {file_name}']
    footer = ['M29']

    if not send_chunk(printer_ip, header):
        print("[ABORT] Failed to send header")
        return

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
                    if not send_chunk(printer_ip, curr_chunk):
                        print("[ABORT] Failed to send chunk")
                        return
                    print(f"[INFO] Sent chunk ending at line {line_number}")
                    time.sleep(3)
                    curr_chunk = []
                    curr_len = 13

        # Final chunk
        if curr_chunk:
            if not send_chunk(printer_ip, curr_chunk):
                print("[ABORT] Failed to send final chunk")
                return
            print(f"[INFO] Sent final chunk up to line {line_number}")

    if not send_chunk(printer_ip, footer):
        print("[ERROR] Failed to send footer")
        return

    print('[SUCCESS] Done sending file to printer')
