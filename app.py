from flask import Flask, render_template, request, jsonify, make_response, send_from_directory
from PrinterToBackend import send_commandd_to_printer, get_responses_from_printer
import mdns
from mdns import printers
from PrinterInfo import Printer


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
    send_commandd_to_printer(printer_ip,commands)

@app.route('/api/status/<printer_ip>', methods=['GET'])
def get_status(printer_ip):
    send_commandd_to_printer(printer_ip, ["M27"])
    response = get_responses_from_printer(printer_ip, 5000)
    data = response.json
    responses = data.get("responses")
    if not responses:
        return jsonify({'error' : 'No responses field'}), 400

    print(responses)
    printers[printer_ip].buffer += responses
    printers[printer_ip].update_printer_variables()

    return jsonify({'status' : printers[printer_ip].printer_status}), 200


if __name__ == '__main__':
    app.run(port=5000, debug=True)