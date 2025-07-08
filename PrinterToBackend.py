import time

import requests
import json
import mdns
from flask import jsonify

def send_commandd_to_printer(printer_ip, commands):
    if not printer_ip or not commands:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        response = requests.post(
            f"http://{printer_ip}/commands",
            json={"commands": commands},
            timeout=5
        )
        if response.status_code == 200:
            return jsonify(response.json()),200
        else:
            return jsonify({"error": f"Printer returned {response.status_code}"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_responses_from_printer(printer_ip, size):
    if not printer_ip or not size:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        time.sleep(1)
        response = requests.get(
            f"http://{printer_ip}/responses",
            json={"size": size},
            timeout=10
        )

        if response.status_code == 200:
            return jsonify(response.json()),200
        else:
            return jsonify({"error": f"Printer returned {response.status_code}"}), 500

    except Exception as e:
        print(f"Printer returned: from exception: {e}",printer_ip)
        return jsonify({"error": str(e)}), 500

def config_printer(printer_ip, baudrate):
    if not printer_ip or not baudrate:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        time.sleep(1)
        response = requests.put(
            f"http://{printer_ip}/machine-config",
            json={"baudrate": baudrate},
            timeout=5
        )
        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify({"error": f"Printer returned {response.status_code}"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500