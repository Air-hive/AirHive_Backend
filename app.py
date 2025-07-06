from flask import Flask, render_template, request, jsonify, make_response, send_from_directory

import PrinterToBackend
import mdns
import PrinterInfo
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

#mDNS Discovery
mdns.go()


#endpoints for the front-end
@app.route('/api/printers', methods=['GET'])
def get_printers():
    with mdns.printer_lock:
        printers = list(mdns.discovered_printers.values())

    # Sort by status (online first)
    printers.sort(key=lambda p: p['status'] != 'online')

    # Convert to JSON serializable format
    for printer in printers:
        printer['last_seen'] = str(printer['last_seen'])

    return jsonify(printers)

@app.route('/api/send-command', methods=['POST'])
def send_commands():
    data = request.json
    printer_ip = data.get('printer_ip')
    commands = data.get('commands')
    PrinterToBackend.send_commandd_to_printer(printer_ip,commands)


if __name__ == '__main__':
    app.run(port=5000, debug=True)