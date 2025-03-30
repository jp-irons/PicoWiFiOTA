import logging
from phew import server
from phew.template import render_template

import ota

from settings import SETTINGS_TEMPLATE_PATH, APP_NAME

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
                "VERSIONS": "https://raw.githubusercontent.com/jp-irons/PicoWiFiOTA/refs/heads/ota/releases/versions.json",
                "BUILDS": "https://raw.githubusercontent.com/jp-irons/PicoWiFiOTA/refs/heads/ota/releases/",
                "CURRENT": ""
            }

            # save the current version
            with open(self.ota_filename, 'w') as f:
                json.dump(self.ota_attributes, f)
        logging.debug('load done')


ota_manager = OTAManager()


@server.route("/settings/ota", methods=["GET"])
@server.route("/settings/ota/", methods=["GET"])
async def ota_home(request):
    logging.debug("ota_home")
    # get ota version and releases
    args = get_args(page='OTA Firmware Settings')
    return await render_template(f"{SETTINGS_TEMPLATE_PATH}/ota_home.html", args=args)


@server.route("/settings/ota/configure", methods=["GET"])
async def ota_configure(request):
    logging.debug("OTA_configure")
    args = get_args(page='Configure OTA Firmware Settings')
    return await render_template(f"{SETTINGS_TEMPLATE_PATH}/ota_configure.html", args=args)


def get_args(page, form=None):
    args = {'app_name': APP_NAME,
            'page': page,
            'form': form}
    return args
