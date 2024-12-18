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
        for ssid, password in wifi_credentials.items():
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

def get_args(page):
    wifi = 'Not connected'
    if wlan_sta.isconnected():
        wifi = wlan_sta.config('ssid')
    ifconfig = wlan_sta.ifconfig()
    ssids = wifi_manager.wlan_attributes['WIFI'].keys()
    args = {'app_name': app_name,
            'page': page,
            'wifi': wifi,
            'ifconfig': ifconfig,
            'ssids': ssids}
    return args


# @server.route('/', methods=['GET', 'POST'])
# async def index(req):
#     return Template('home.html').render(page='Index')
#
#

@server.route('/')
async def home(req):
    args = get_args(page='Home')
    return Template('home.html').render(args)


@server.route('/configure_wifi', methods=['GET', 'POST'])
async def configure_wifi(req):
    args = get_args(page='Configure Wi-Fi')
    return Template('configure_wifi.html').render(args)

@server.route('/remove_ssid', methods=['GET', 'POST'])
async def remove_ssid(req):
    args = get_args(page='Remove SSID')
    form = req.form
    args['form'] = form
    for key, value in form.items():
        ssid = key
        action = form[ssid]
        args['ssid'] = ssid
        if 'Delete' == action:
            print('Delete', ssid)
            return Template('remove_ssid.html').render(args)
        if 'Confirm' == action:
            print('Confirm', ssid)
            wifi_manager.wlan_attributes['WIFI'].pop(ssid)
            return Template('configure_wifi.html').render(args)
        if 'Cancel' == action:
            print('Cancel', ssid)
            return Template('configure_wifi.html').render(args)
    return Template('page2.html').render(args)

@server.route('/page2')
async def page2(req):
    args = get_args(page='Page 2')
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
    recompile()
    asyncio.run(run_app())


async def main():
    # connect_wifi()
    pass

def rmdir(dir):
    for i in os.listdir(dir):
        os.remove('{}/{}'.format(dir,i))
    os.rmdir(dir)

def recompile(dir='templates'):
    for i in os.listdir(dir):
        filename = str(i)
        if '.py' in filename:
            print('Removed ', filename)
            os.remove('{}/{}'.format(dir,i))

def rmtemplates():
    rmdir('templates')

if __name__ == '__main__':
    main()
