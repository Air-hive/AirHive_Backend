import threading
import time
from flask import Flask, render_template, request, jsonify, make_response, send_from_directory
from PrinterToBackend import send_commandd_to_printer, get_responses_from_printer
import mdns
from mdns import printers
from UploadFileToPrinter import upload_file_to_printer
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class JobModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    priority = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "priority": self.priority
        }


# mDNS Discovery
mdns.go()


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


@app.route('/api/send-command/<printer_ip>', methods=['POST'])
def send_commands(printer_ip):
    data = request.json
    commands = data.get('commands')
    response = send_commandd_to_printer(printer_ip, commands)
    response_obj, status = response
    update_printer_responses(printer_ip)
    return response_obj.get_json(), 200

@app.route('/api/update-responses/<printer_ip>', methods=['GET'])
def update_printer_responses(printer_ip):
    printer = printers[printer_ip]
    response = get_responses_from_printer(printer_ip, 5000)

    response_obj, status = response
    data = response_obj.get_json()
    responses = data.get("responses")
    if responses:
        printer.buffer += responses
        printer.update_printer_variables()

    return jsonify({'all_responses': "updated"}), status

@app.route('/api/raw-responses/<printer_ip>', methods=['GET'])
def get_raw_responses(printer_ip):
    printer = printers[printer_ip]
    response = get_responses_from_printer(printer_ip, 5000)

    response_obj, status = response
    data = response_obj.get_json()
    responses = data.get("responses")
    if responses:
        printer.buffer += responses
        printer.update_printer_variables()
    raw_buffer_copy = printer.raw_buffer
    printer.clear_raw_buffer()

    return jsonify({'raw_responses': raw_buffer_copy}), status

@app.route('/api/status/<printer_ip>', methods=['GET'])
def get_status(printer_ip):
    printer = printers[printer_ip]
    response = send_commandd_to_printer(printer_ip, ["M27"])
    response_obj, status = response
    update_printer_responses(printer_ip)
    return jsonify({'status': printer.printer_status,
                    'Progress': printer.print_progress}), status


@app.route('/api/temperature/<printer_ip>', methods=['GET'])
def get_temperature(printer_ip):
    printer = printers[printer_ip]
    response = send_commandd_to_printer(printer_ip, ["M105"])
    response_obj, status = response
    update_printer_responses(printer_ip)
    return jsonify({'hotend_temperature': printer.hotend_temperature,
                    'heatbed_temperature': printer.heatbed_temperature
                    }), status


@app.route('/api/elapsed-time/<printer_ip>', methods=['GET'])
def get_print_elapsed_time(printer_ip):
    printer = printers[printer_ip]
    response = send_commandd_to_printer(printer_ip, ["M31"])
    response_obj, status = response
    update_printer_responses(printer_ip)
    return jsonify({'elapsed_time': printer.elapsed_time}), status


@app.route('/api/home/<printer_ip>', methods=['POST'])
def home_axis(printer_ip):
    data = request.json
    axis_to_home = data.get('axis-to-home')
    printer = printers[printer_ip]
    command = "G28"
    for axis in axis_to_home:
        if axis == "all":
            break
        if axis == "X":
            command += " X"
        elif axis == "Y":
            command += " Y"
        elif axis == "Z":
            command += " Z"
        else:
            command = ""
            return jsonify({'error': 'Wrong json fields'}), 400
    response = send_commandd_to_printer(printer_ip, [command])
    response_obj, status = response
    update_printer_responses(printer_ip)
    return jsonify({'x_coordinate': printer.x_coordinate,
                    'y_coordinate': printer.y_coordinate,
                    'z_coordinate': printer.z_coordinate
                    }), status


# G0 X10 Y20 Z0.3 F3000
@app.route('/api/move_axis/<printer_ip>', methods=['POST'])
def move_axis(printer_ip):
    data = request.json
    x_distance = data.get('x_distance')
    y_distance = data.get('y_distance')
    z_distance = data.get('z_distance')
    e_distance = data.get('e_distance')

    printer = printers[printer_ip]
    command = "G0"
    if x_distance:
        command += f" X{x_distance} F1500"
    if y_distance:
        command += f" Y{y_distance} F1500"
    if z_distance:
        command += f" Z{z_distance} F300"
    if e_distance:
        command += f" E{e_distance}"

    response = send_commandd_to_printer(printer_ip, ["G91", command])
    response_obj, status = response
    update_printer_responses(printer_ip)

    return jsonify({'x_coordinate': printer.x_coordinate,
                    'y_coordinate': printer.y_coordinate,
                    'z_coordinate': printer.z_coordinate,
                    'e_coordinate': printer.E_coordinate}), status


@app.route('/api/axis-coordinates/<printer_ip>', methods=['GET'])
def get_axis_coordinates(printer_ip):
    printer = printers[printer_ip]
    response = send_commandd_to_printer(printer_ip, ["M114"])
    response_obj, status = response
    update_printer_responses(printer_ip)
    return jsonify({'X': printer.x_coordinate,
                    'Y': printer.y_coordinate,
                    'Z': printer.z_coordinate,
                    }), status


@app.route('/api/disable-motors/<printer_ip>', methods=['POST'])
def disable_motors(printer_ip):
    command = "M84"
    response = send_commandd_to_printer(printer_ip, ["G91", command])
    response_obj, status = response
    update_printer_responses(printer_ip)
    return jsonify({'Status': "Motors off"}), status


@app.route('/api/sdcard-files/<printer_ip>', methods=['GET'])
def sdcard_files(printer_ip):
    response = send_commandd_to_printer(printer_ip, ["M20"])
    response_obj, status = response
    update_printer_responses(printer_ip)
    return jsonify({'sdcard-files': printers[printer_ip].sd_card_files}), status


@app.route('/api/upload-to-sdcard/<printer_ip>', methods=['POST'])
def upload_to_sdcard(printer_ip):
    data = request.json
    upload_file_to_printer(printer_ip, data)
    update_printer_responses(printer_ip)
    return jsonify({'sdcard-files': printers[printer_ip].sd_card_files}), 200


@app.route('/api/print-file/<printer_ip>', methods=['POST'])
def print_file(printer_ip):
    data = request.json
    filename = data.get('filename')
    response = send_commandd_to_printer(printer_ip, ["M21", f"M23 {filename}", "M24"])
    response_obj, status = response
    update_printer_responses(printer_ip)
    return jsonify({'Printing': filename}), status


# --------------------------------------------------------------------------------------------------------

# --- Create (POST) ---
@app.route('/api/jobs', methods=['POST'])
def create_job():
    data = request.json
    file_name = data.get('file_name')
    file_path = data.get('file_path')
    priority = data.get('priority')

    if not file_name or not file_path or not priority:
        return jsonify({'error': "Missing file name or file path or priority"}), 400

    new_job = JobModel(
        file_name=file_name,
        file_path=file_path,
        priority=priority
    )

    db.session.add(new_job)
    db.session.commit()
    return jsonify(new_job.to_dict()), 201


# --- Read All (GET) ---
@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    jobs = JobModel.query.all()
    return jsonify([job.to_dict() for job in jobs])


# --- Read One (GET) ---
@app.route('/api/jobs/<int:job_id>', methods=['GET'])
def get_job(job_id):
    job = JobModel.query.get_or_404(job_id)
    return jsonify(job.to_dict())


# --- Update (PUT) ---
@app.route('/api/jobs/<int:job_id>', methods=['PUT'])
def update_job(job_id):
    job = JobModel.query.get_or_404(job_id)
    data = request.get_json()
    job.file_name = data.get('file_name', job.file_name)
    job.file_path = data.get('file_path', job.file_path)
    job.priority = data.get('priority', job.priority)
    db.session.commit()
    return jsonify(job.to_dict())


# --- Delete (DELETE) ---
@app.route('/api/jobs/<int:job_id>', methods=['DELETE'])
def delete_job(job_id):
    job = JobModel.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    return jsonify({"message": "Job deleted"})


# --- Initialize Database ---
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(port=5000, debug=True)
