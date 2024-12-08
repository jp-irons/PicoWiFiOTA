import sys
# import micropython_ota
import network
import socket
import requests
import time
import json
import os
import ulogging as logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

wlan_sta = network.WLAN(network.STA_IF)

class WiFiConfigManager:
    """ This class handles OTA updates. It connects to the Wi-Fi, checks for updates, downloads and installs them."""
    def __init__(self, wlan_filename ='WIFI_CONFIG.json'):
        self.wlan_filename = wlan_filename
        self.wlan_attributes = None
        self.load()

    def load(self):
        if self.wlan_filename in os.listdir():
            with open(self.wlan_filename) as f:
                self.wlan_attributes = json.load(f)
            f.close()
        else:
            self.wlan_attributes = {
                'WIFI': []
                # "WIFI": [
                #     {
                #         'SSID': 'jamnethome',
                #         "PASSWORD": 'password'
                #     }
                # ]
            }
            # save the current version
            with open(self.wlan_filename, 'w') as f:
                json.dump(self.wlan_attributes, f)

    def connect_to(self, ssid, password):
        logger.debug('Trying to connect to %s...' % ssid)
        wlan_sta.connect(ssid, password)
        for retry in range(100):
            connected = wlan_sta.isconnected()
            if connected:
                print()
                return connected
            time.sleep(0.1)
            print('.', end='')
        print()

    def connect(self):
        logger.debug('connect()')
        wifi_credentials = self.wlan_attributes['WIFI']
        wlan_sta.active(True)
        connected = False
        if wlan_sta.isconnected():
            logger.info('Connected: ', wlan_sta.ifconfig())
            return True
        for wap_credentials in wifi_credentials:
            ssid = wap_credentials['SSID']
            password = wap_credentials['PASSWORD']
            connected = self.connect_to(ssid, password)
            if connected:
                logger.info('Connected to ', ssid, wlan_sta.ifconfig())
                return connected
            else:
                logger.info('Failed to connect to ' + ssid)
        logger.debug('Need to set up AP and get credentials')
        return connected

wifi_config = WiFiConfigManager()

def test_config_manager():
    wifi_config.connect()

def disconnect_wifi():
    wlan_sta.active(True)
    if not wlan_sta.isconnected():
        return None
    wlan_sta.disconnect()



def http_get(host='', path=''):
    # url = 'https://1drv.ms/t/s!AgUtKRuWyBCtloRNgOC4MIRUXVGVAQ?e=IzeAwW'
    # url = 'https://drive.google.com/file/d/14rSq2J_wrDV_qIotLTCFt5TPppJ2iQHk/view?usp=drive_link'
    #url='https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd'
    url = 'http://storagepi.local/ota'
    path = '/ota/a.html'

    print(url)
    response = requests.get(url)
    # Get response code
    response_code = response.status_code
    print(response_code)
    # Get response content
    response_content = response.content
    print(response_content)


def check_for_update():
    # connect_wifi()
    # update_to_latest_version()
    pass


def main():
    # connect_wifi()
    pass


if __name__ == '__main__':
    main()
