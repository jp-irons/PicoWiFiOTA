# import micropython_ota
import network
import json
import os
import logging as logging
import asyncio

from microdot import Microdot, Response, send_file
from microdot.utemplate import Template

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

wlan_sta = network.WLAN(network.STA_IF)


async def connect_to(ssid, password):
    logger.debug('Trying to connect to %s...' % ssid)
    wlan_sta.connect(ssid, password)
    for retry in range(100):
        connected = wlan_sta.isconnected()
        if connected:
            print()
            return connected
        await asyncio.sleep(0.1)
        print('.', end='')
    print()


class WiFiManager:
    def __init__(self, wlan_filename='WIFI_CONFIG.json'):
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

    async def connect(self):
        logger.debug('connect()')
        wifi_credentials = self.wlan_attributes['WIFI']
        wlan_sta.active(True)
        connected = False
        if wlan_sta.isconnected():
            logger.info('Connected: %s', wlan_sta.ifconfig())
            return True
        for wap_credentials in wifi_credentials:
            ssid = wap_credentials['SSID']
            password = wap_credentials['PASSWORD']
            connected = await connect_to(ssid, password)
            if connected:
                logger.info('Connected to %s %s', ssid, wlan_sta.ifconfig())
                return connected
            else:
                logger.info('Failed to connect to ' + ssid)
        logger.debug('Need to set up AP and get credentials')
        return connected


server = Microdot()
Response.default_content_type = 'text/html'
app_name = "Pi Pico Embedded"


# @server.route('/', methods=['GET', 'POST'])
# async def index(req):
#     return Template('index.html').render(page='Index')
#
#

@server.route('/static/<path:path>')
async def static(request, path):
    if '..' in path:
        # directory traversal is not allowed
        return 'Not found', 404
    return send_file('static/' + path)

@server.route('/')
async def index(req):
    args = {'app_name': app_name, 'page': 'Index'}
    return Template('index.html').render(args)


@server.route('/page1')
async def page1(req):
    args = {'app_name': app_name, 'page': 'Page 1'}
    return Template('page1.html').render(args)


@server.route('/page2')
async def page2(req):
    args = {'app_name': app_name, 'page': 'Page 2'}
    return Template('page2.html').render(args)


wifi_manager = WiFiManager()

async def run_app():
    await wifi_manager.connect()
    logger.debug('starting app')
    await asyncio.gather(server.start_server(port=80))
    logger.debug('app finished')


def disconnect_wifi():
    wlan_sta.active(True)
    if not wlan_sta.isconnected():
        return None
    wlan_sta.disconnect()

def execute():
    asyncio.run(run_app())


async def main():
    # connect_wifi()
    pass

def rmdir(dir):
    for i in os.listdir(dir):
        os.remove('{}/{}'.format(dir,i))
    os.rmdir(dir)

if __name__ == '__main__':
    main()
