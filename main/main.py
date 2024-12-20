# import micropython_ota
import network
import json
import os
import logging as logging
# import asyncio
import uasyncio as asyncio

from microdot import Microdot, Response, send_file
from microdot.utemplate import Template

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class WiFiManager():
    def __init__(self, wlan_filename='WIFI_CONFIG.json'):
        self.wlan_filename = wlan_filename
        self.wlan_attributes = None
        self.wlan_sta = network.WLAN(network.STA_IF)
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
                #         'myssid' : 'password'
                #     }
                # ]
            }
            # save the current version
            with open(self.wlan_filename, 'w') as f:
                json.dump(self.wlan_attributes, f)

    async def setup_connection(self):
        logger.debug('connect()')
        wifi_credentials = self.wlan_attributes['WIFI']
        self.wlan_sta.active(True)
        connected = False
        if self.wlan_sta.isconnected():
            logger.info('Connected: %s', self.wlan_sta.ifconfig())
            return True
        for ssid, password in wifi_credentials.items():
            connected = await self.connect_to(ssid, password)
            if connected:
                logger.info('Connected to %s %s', ssid, self.wlan_sta.ifconfig())
                return connected
            else:
                logger.info('Failed to connect to ' + ssid)
        logger.debug('Need to set up AP and get credentials')
        return connected

    async def connect_to(self, ssid, password):
        logger.debug('Trying to connect to %s...' % ssid)
        self.wlan_sta.connect(ssid, password)
        for retry in range(100):
            connected = self.wlan_sta.isconnected()
            if connected:
                print()
                return connected
            await asyncio.sleep(0.1)
            print('.', end='')
        print()

    async def scan_for_waps(self):
        logger.debug('Scanning for Wi-Fi networks')
        networks = self.wlan_sta.scan()
        return networks


    def get_host(self):
        return self.wlan_sta.ifconfig()[0]

    async def scan_for_waps_sorted(self):
        waps = await self.scan_for_waps()
        waps.sort(reverse=True, key=lambda x: x[3])
        wap_list = []
        ssid_list = []
        for wap in waps:
            ssid_name = str(wap[0], 'utf-8')
            ssid_signal = wap[3]
            if ssid_name is not '' and ssid_name not in ssid_list:  # hidden
                ssid_list.append(ssid_name)
                wap_list.append((ssid_name, ssid_signal))
        return wap_list


wifi_manager = WiFiManager()

server = Microdot()
Response.default_content_type = 'text/html'
app_name = "Pi Pico Embedded"

def get_args(page):
    wifi = 'Not connected'
    if wifi_manager.wlan_sta.isconnected():
        wifi = wifi_manager.wlan_sta.config('ssid')
    ifconfig = wifi_manager.wlan_sta.ifconfig()
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
    args['waps'] = await wifi_manager.scan_for_waps_sorted()
    return Template('configure_wifi.html').render(args)

@server.route('/add_ssid', methods=['GET', 'POST'])
async def add_ssid(req):
    logger.debug('add_ssid')
    args = get_args(page='Add SSID')
    form = req.form
    action = form['action']
    logger.debug('add_ssid ' + action)
    if 'Add' == action:
        ssid = form['ssid']
        logger.debug('add_ssid ' + ssid)
        password = form['password']
        wifi_manager.wlan_attributes['WIFI'][form['ssid']] = form['password']
    args['form'] = form
    args['waps'] = await wifi_manager.scan_for_waps_sorted()
    return Template('configure_wifi.html').render(args)

@server.route('/remove_ssid', methods=['GET', 'POST'])
async def remove_ssid(req):
    args = get_args(page='Remove SSID')
    form = req.form
    args['form'] = form
    print(form)
    action = form['action']
    logger.debug('remove_ssid: ' + action)
    if 'Delete' == action:
        ssid = form['ssid']
        logger.debug('remove_ssid deleting '  + ', ssid: ' + ssid )
        args['ssid'] = ssid
        return Template('remove_ssid.html').render(args)
    if 'Confirm' == action:
        ssid = form['ssid']
        args['ssid'] = ssid
        logger.debug('remove_ssid confirmed delete '  + ', ssid: ' + ssid )
        wifi_manager.wlan_attributes['WIFI'].pop(ssid)
        args['waps'] = await wifi_manager.scan_for_waps_sorted()
        return Template('configure_wifi.html').render(args)
    if 'Cancel' == action:
        logger.debug('remove_ssid Cancel')
        args['waps'] = await wifi_manager.scan_for_waps_sorted()
        return Template('configure_wifi.html').render(args)
    logger.debug('remove_ssid default')
    return Template('page2.html').render(args)

@server.route('/page2')
async def page2(req):
    args = get_args(page='Page 2')
    return Template('page2.html').render(args)



async def run_app():
    await wifi_manager.setup_connection()
    logger.debug('starting app')
    ssl = None
    port = 80
    if ssl is None:
        if port == 80:
            logger.info('http://'+wifi_manager.get_host())
        else:
            logger.info('http://' + wifi_manager.get_host() + ':' + str(port))
    else:
        if port == 443:
            logger.info('https://'+wifi_manager.get_host())
        else:
            logger.info('http://' + wifi_manager.get_host() + ':' + str(port))

    await asyncio.gather(server.start_server(port=80))
    logger.debug('app finished')


def disconnect_wifi():
    wifi_manager.wlan_sta.active(True)
    if not wifi_manager.wlan_sta.isconnected():
        return None
    wifi_manager.wlan_sta.disconnect()

def execute():
    recompile()
    asyncio.run(run_app())

def debug():
    logger.setLevel(logging.DEBUG)
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
            logger.info('Removed ' + filename)
            os.remove('{}/{}'.format(dir,i))

def rmtemplates():
    rmdir('templates')

if __name__ == '__main__':
    main()
