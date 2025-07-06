from zeroconf import ServiceBrowser, Zeroconf
import time
import threading
from PrinterInfo import Printer

discovered_printers = {}
printer_lock = threading.Lock()
printers = {}

class PrinterServiceListener:
    def __init__(self):
        self.printers = {}

    def add_service(self, zeroconf, service_type, name):
        if name.startswith('Airhive'):
            try:
                info = zeroconf.get_service_info(service_type, name)
                if info:
                    addresses = info.parsed_addresses()

                    # Handle properties safely
                    properties = {}
                    if info.properties:
                        for key, value in info.properties.items():
                            try:
                                key_str = key.decode('utf-8')
                                value_str = value.decode('utf-8') if value else ""
                                properties[key_str] = value_str
                            except:
                                # Skip problematic properties
                                pass

                    printer_data = {
                        'name': name,
                        'hostname': info.server,
                        'ip': addresses[0] if addresses else None,
                        'port': info.port,
                        'properties': properties,
                        'last_seen': time.time(),
                        'status': 'online',
                        'temperatures': {
                            'hotend': {'current': 0, 'target': 0},
                            'bed': {'current': 0, 'target': 0}
                        }
                    }

                    with printer_lock:
                        discovered_printers[name] = printer_data
                        printers[printer_data['ip']] = Printer()

                    print(f"Added printer: {name} at {printer_data['ip']}")
            except Exception as e:
                print(f"Error adding service {name}: {str(e)}")

    def remove_service(self, zeroconf, service_type, name):
        if name.startswith('Airhive'):
            with printer_lock:
                if name in discovered_printers:
                    # Mark as offline but keep in list
                    discovered_printers[name]['status'] = 'offline'
                    print(f"Printer marked offline: {name}")

    def update_service(self, zeroconf, service_type, name):
        self.add_service(zeroconf, service_type, name)

def start_zeroconf_discovery():
    zeroconf = Zeroconf()
    listener = PrinterServiceListener()
    browser = ServiceBrowser(zeroconf, "_http._tcp.local.", listener)
    print("Starting mDNS discovery for Airhive printers...")

    # Keep the discovery running in the background
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        zeroconf.close()

def go():
    discovery_thread = threading.Thread(target=start_zeroconf_discovery, daemon=True)
    discovery_thread.start()
