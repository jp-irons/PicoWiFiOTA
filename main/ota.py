import json

import logging

OTA_FILE = "config/ota.json"

class OTAManager:
    def __init__(self, ota_filename=OTA_FILE):
        self.ota_filename = ota_filename
        self.ota_attributes = None
        self.load()

    def load(self):
        logging.debug('load')
        try:
            logging.debug('opening ' + self.ota_filename)
            with open(self.ota_filename) as f:
                self.ota_attributes = json.load(f)
            f.close()
            logging.debug('opened ' + self.ota_filename)
        except OSError:  # open failed
            logging.debug('open failed for ' + self.ota_filename)
            # handle the file open case
            self.ota_attributes = {
                "OTA_PATH": "https://github.com/jp-irons/PicoWiFiOTA/raw/refs/heads/ota/releases/",
                "VERSIONS": "versions.json"
            }

            # save the current version
            with open(self.ota_filename, 'w') as f:
                json.dump(self.ota_attributes, f)
        logging.debug('load done')


ota_manager = OTAManager()

