
def calculate_checksum(line):
    cs = 0
    for c in line:
        cs ^= ord(c)
    return cs

def format_gcode_line(line, line_number):
    # Remove comment part

    # Format with line number and checksum
    gcode = f'N{line_number} {line}'
    checksum = calculate_checksum(gcode)
    return f'{gcode}*{checksum}'

commands = ["G28","M105","G28"]
curr_line = 1
for command in commands:
    print(format_gcode_line(command,curr_line))
    curr_line += 1

# "M110 N0"
# "M28 filename"
# "N1 G28*18"
# "N2 M105*37"
# "N3 G28*16"
# "M29"