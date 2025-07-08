import time
import requests
from flask import jsonify

MAX_RETRIES = 5
RETRY_DELAY = 0.1  # seconds

def send_commandd_to_printer(printer_ip, commands):
    if not printer_ip or not commands:
        return jsonify({"error": "Missing parameters"}), 400

    url = f"http://{printer_ip}/commands"
    payload = {"commands": commands}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(url, json=payload, timeout=5)

            if response.status_code == 200:
                return jsonify(response.json()), 200
            else:
                # print(f"[Attempt {attempt}] Printer returned status {response.status_code}")
                return jsonify({"error": f"Printer returned {response.status_code}"}), 500

        except requests.exceptions.RequestException as e:
            # print(f"[Attempt {attempt}] send_commandd_to_printer error: {e}")
            if attempt == MAX_RETRIES:
                return jsonify({"error": str(e)}), 500
            time.sleep(RETRY_DELAY)


def get_responses_from_printer(printer_ip):
    if not printer_ip:
        return jsonify({"error": "Missing parameters"}), 400

    url = f"http://{printer_ip}/responses"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                return jsonify(response.json()), 200
            else:
                # print(f"[Attempt {attempt}] Printer returned status {response.status_code}")
                return jsonify({"error": f"Printer returned {response.status_code}"}), 500

        except requests.exceptions.RequestException as e:
            # print(f"[Attempt {attempt}] get_responses_from_printer error: {e}")
            if attempt == MAX_RETRIES:
                return jsonify({"error": str(e)}), 500
            time.sleep(RETRY_DELAY)

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