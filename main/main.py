# import micropython_ota
import network
import json
import os
import logging
# import asyncio
import uasyncio as asyncio
from phew import server
from phew.template import render_template

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

APP_NAME = "Pi Pico Embedded"
AP_DOMAIN = "pipico.net"

CONTENT_PATH = "content"
IMAGES_PATH = "content/images"
WIFI_TEMPLATE_PATH = "content/wi-fi"
APP_TEMPLATE_PATH = "content/app"
WIFI_FILE = "config/wifi.json"
WIFI_MAX_ATTEMPTS = 3


class WiFiManager():
    def __init__(self, wlan_filename=WIFI_FILE):
        self.wlan_filename = wlan_filename
        self.wlan_attributes = None
        self.ssids = None
        self.sta = network.WLAN(network.STA_IF)
        self.sta.disconnect()
        self.sta.active(False)
        self.sta_connecting = False
        self.ap = network.WLAN(network.AP_IF)
        self.ap.disconnect()
        self.ap.active(False)
        self.load()
        if 'HOSTNAME' in self.wlan_attributes:
            network.hostname(str(self.wlan_attributes['HOSTNAME']))

    def load(self):
        logger.debug('load')
        try:
            logger.debug('opening ' + self.wlan_filename)
            with open(self.wlan_filename) as f:
                self.wlan_attributes = json.load(f)
            f.close()
            logger.debug('opened ' + self.wlan_filename)
        except OSError:  # open failed
            logger.debug('open failed for ' + self.wlan_filename)
            # handle the file open case
            self.wlan_attributes = {
                'WIFI': [],
                "HOSTNAME": "pi_pico_w",
                "PASSWORD": "p1c0wifi",
                "RUNWAP": "always",
                "RUNWAP_CHOICES": ["always", "as needed", "never"]
            }
            # save the current version
            with open(self.wlan_filename, 'w') as f:
                json.dump(self.wlan_attributes, f)
        self.ssids = list(self.wlan_attributes['WIFI'])
        self.ssids.sort(key=lambda x: x[0])

    def save(self):
        logger.debug('save')
        self.update_ssid_order()
        self.wlan_attributes['WIFI'] = self.ssids
        with open(self.wlan_filename, 'w') as f:
            json.dump(self.wlan_attributes, f)

    async def setup_connection(self):
        logger.debug('connect()')
        self.sta.active(True)
        connected = False
        if self.sta.isconnected():
            logger.info('Connected: %s', self.sta.ifconfig())
            return True
        self.sta_connecting = True
        for credentials in self.ssids:
            ssid = credentials[1]
            password = credentials[2]
            connected = await self.connect_to(ssid, password)
            if connected:
                logger.info('Connected to %s %s', ssid, self.sta.ifconfig())
                log_serverUrl()
                return connected
            else:
                logger.info('Failed to connect to ' + ssid)
        logger.debug('No Wi-FI connection made')
        self.sta_connecting = False
        return connected

    async def connect_to(self, ssid, password):
        logger.debug('Trying to connect to %s...' % ssid)
        self.sta.connect(ssid, password)
        for retry in range(100):
            connected = self.sta.isconnected()
            if connected:
                print()
                return connected
            await asyncio.sleep(0.1)
            print('.', end='')
        print()

    def scan_for_waps(self):
        logger.debug('Scanning for Wi-Fi networks')
        networks = self.sta.scan()
        return networks

    def get_host(self):
        return self.sta.ifconfig()[0]

    def scan_for_waps_sorted(self):
        visible_ssids = self.scan_for_waps()
        visible_ssids.sort(reverse=True, key=lambda x: x[3])
        wap_list = []
        ssid_list = []
        for visible_ssid in visible_ssids:
            ssid_name = str(visible_ssid[0], 'utf-8')
            ssid_signal = visible_ssid[3]
            if ssid_name is not '' and ssid_name not in ssid_list:  # hidden
                ssid_list.append(ssid_name)
                wap_list.append((ssid_name, ssid_signal))
        return wap_list

    def insert_ssid(self, new_ssid, new_password):
        self.ssids.insert(0, ['0', new_ssid, new_password])
        self.update_ssid_order()

    def update_ssid_order(self):
        for i, ssid in enumerate(self.ssids):
            self.ssids[i][0] = str(i)

    def move_ssid_to(self, index, new_index):
        if (index < 0 or
                new_index < 0 or
                index > len(self.ssids) or
                new_index > len(self.ssids)):
            return
        this_ssid = self.ssids.pop(index)
        self.ssids.insert(new_index, this_ssid)
        self.update_ssid_order()

    async def run_wap_loop(self):
        logger.debug('run_wap_loop')
        while True:
            if not self.ap_required():
                self.ap.active(False)
            else:
                await self.start_ap()
            await asyncio.sleep(4)

    async def start_ap(self):
        # ap is required
        if self.ap.active():
            return
        ssid = wifi_manager.wlan_attributes['HOSTNAME']
        password = wifi_manager.wlan_attributes['PASSWORD']
        self.ap.config(essid=ssid, password=password)
        self.ap.active(True)
        while not self.ap.active():
            await asyncio.sleep_ms(10)
            print('.', end='')
        print()
        logger.info('AP active - SSID:' + ssid + ' password:' + password + ' IP:' + str(self.ap.ifconfig()[0]))

    def ap_required(self):
        # if ap required but not operational start ap
        if self.wlan_attributes['RUNWAP'] == 'always':
            return True
        if self.sta_connecting:
            return False
        if self.wlan_attributes['RUNWAP'] == 'as needed':
            return True
        return False


wifi_manager = WiFiManager()


#app_name = "Pi Pico Embedded"

def get_args(page, form=None):
    wifi_sta = 'Not connected'
    wifi_sta_connected = wifi_manager.sta.isconnected()
    if wifi_sta_connected:
        wifi_sta = wifi_manager.sta.config('ssid')
    wifi_ap = wifi_manager.wlan_attributes["HOSTNAME"]
    wifi_ap_password = wifi_manager.wlan_attributes["PASSWORD"]
    wifi_ap_connected = wifi_manager.ap.isconnected()
    ifconfig = wifi_manager.sta.ifconfig()
    ssids = wifi_manager.ssids
    args = {'app_name': APP_NAME,
            'page': page,
            'wifi_sta': wifi_sta,
            'wifi_sta_connected': wifi_sta_connected,
            'wifi_ap': wifi_ap,
            'wifi_ap_password': wifi_ap_password,
            'wifi_ap_connected': wifi_ap_connected,
            'wifi_ap_required': wifi_manager.wlan_attributes["RUNWAP"],
            'wifi_ap_choices': wifi_manager.wlan_attributes["RUNWAP_CHOICES"],
            'ifconfig': ifconfig,
            'ssids': ssids,
            'form': form}
    return args


# @server.route('/', methods=['GET', 'POST'])
# async def curr_index(req):
#     return Template('home.html').render(page='Index')
#
#

# catchall example
@server.catchall()
def catchall(request):
    args = get_args(page='Not found error: 404')
    args['url'] = request.uri
    return render_template(f"{CONTENT_PATH}/unexpected.html", args=args), 404


# url parameter and template render
@server.route("/", methods=["GET"])
def home(request):
    args = get_args(page='Home')
    return render_template(f"{CONTENT_PATH}/home.html", args=args)


# return file in IMAGES_PATH
@server.route("/images/<file_name>", methods=['GET', 'POST'])
def images(request, file_name):
    file_path = f"{IMAGES_PATH}/{file_name}"
    logger.debug('getting image ' + file_path)
    page = open(file_path, "rb")
    content = page.read()
    page.close()
    return content, 200


# url parameter and template render
@server.route("/wi-fi", methods=["GET"])
def home(request):
    args = get_args(page='Wi-Fi Home')
    return render_template(f"{WIFI_TEMPLATE_PATH}/home.html", args=args)


@server.route('/wi-fi/configure_wifi', methods=['GET', 'POST'])
def configure_wifi(req):
    args = get_args(page='Configure Wi-Fi')
    args['waps'] = wifi_manager.scan_for_waps_sorted()
    return render_template(f"{WIFI_TEMPLATE_PATH}/configure_wifi.html", args=args)


@server.route('/wi-fi/add_ssid', methods=['GET', 'POST'])
def add_ssid(req):
    logger.debug('add_ssid')
    form = req.form
    action = form['action']
    if 'Add' == action:
        new_ssid = form['ssid']
        logger.debug('add_ssid ' + new_ssid)
        new_password = form['password']
        wifi_manager.insert_ssid(new_ssid, new_password)
    args = get_args(page='Add SSID', form=form)
    args['waps'] = wifi_manager.scan_for_waps_sorted()
    return render_template(f"{WIFI_TEMPLATE_PATH}/configure_wifi.html", args=args)


@server.route('/wi-fi/update_ssid', methods=['GET', 'POST'])
def update_ssid(req):
    logger.debug('remove_ssid ')
    form = req.form
    ssid_index = form['ssid_index']
    try:
        index = int(ssid_index)
        action = form['action']
        if 'Remove' == action:
            logger.debug('update_ssid removing ssid ' + str(index))
            wifi_manager.ssids.pop(index)
        if 'v' == action:
            logger.debug('update_ssid ssid down ' + str(index))
            wifi_manager.move_ssid_to(index, index + 1)
        if '^' == action:
            logger.debug('update_ssid ssid up ' + str(index))
            wifi_manager.move_ssid_to(index, index - 1)

    except ValueError:
        logger.error('remove ssid invalid curr_index' + ssid_index)
    except IndexError:
        logger.error('remove ssid curr_index out of range' + ssid_index)
    args = get_args(page='Remove SSID', form=form)
    args['waps'] = wifi_manager.scan_for_waps_sorted()
    return render_template(f"{WIFI_TEMPLATE_PATH}/configure_wifi.html", args=args)


@server.route('/wi-fi/update_config', methods=['GET', 'POST'])
def update_config(req):
    logger.debug('update_config ')
    form = req.form
    action = form['action']
    if 'Reload' == action:
        logger.debug('update_config Reload')
        wifi_manager.load()
    if 'Save' == action:
        logger.debug('update_config Save')
        wifi_manager.save()
    args = get_args(page='Configure Wi-Fi')
    args['waps'] = wifi_manager.scan_for_waps_sorted()
    return render_template(f"{WIFI_TEMPLATE_PATH}/configure_wifi.html", args=args)


# @server.route('/page2')
# async def page2(req):
#     args = get_args(page='Page 2')
#     return Template('page2.html').render(args)

def log_serverUrl():
    ssl = None
    port = 80
    if ssl is None:
        if port == 80:
            logger.info('http://' + wifi_manager.get_host())
        else:
            logger.info('http://' + wifi_manager.get_host() + ':' + str(port))
    else:
        if port == 443:
            logger.info('https://' + wifi_manager.get_host())
        else:
            logger.info('http://' + wifi_manager.get_host() + ':' + str(port))


async def start_server(host="0.0.0.0", port=80):
    logger.debug('start server')
    server.run(host, port)


async def run_app():
    logger.debug('starting app')
    port = 80
    await asyncio.gather(
        wifi_manager.setup_connection(),
        wifi_manager.run_wap_loop(),
        start_server(port=port)
    )
    logger.debug('app finished')


def disconnect_wifi():
    wifi_manager.sta.active(True)
    if not wifi_manager.sta.isconnected():
        return None
    wifi_manager.sta.disconnect()


def execute():
    asyncio.run(run_app())


def debug():
    logger.setLevel(logging.DEBUG)
    asyncio.run(run_app())


async def main():
    # connect_wifi()
    pass


def rmdir(dir_name):
    for i in os.listdir(dir_name):
        os.remove('{}/{}'.format(dir_name, i))
    os.rmdir(dir_name)


def rm_templates():
    rmdir('content')


if __name__ == '__main__':
    main()
