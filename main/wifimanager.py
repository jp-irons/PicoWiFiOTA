import json
import network
import uasyncio as asyncio

import logging
from main import APP_NAME
from phew import server
from phew.template import render_template

WIFI_TEMPLATE_PATH = "content/settings"
WIFI_FILE = "config/wifi.json"
WIFI_MAX_ATTEMPTS = 3
WIFI_MAX_SSIDS = 5

class WiFiManager:
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
        logging.debug('load')
        try:
            logging.debug('opening ' + self.wlan_filename)
            with open(self.wlan_filename) as f:
                self.wlan_attributes = json.load(f)
            f.close()
            logging.debug('opened ' + self.wlan_filename)
        except OSError:  # open failed
            logging.debug('open failed for ' + self.wlan_filename)
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
        logging.debug('save')
        self.update_ssid_order()
        self.wlan_attributes['WIFI'] = self.ssids
        with open(self.wlan_filename, 'w') as f:
            json.dump(self.wlan_attributes, f)

    async def setup_connection(self):
        logging.debug('connect()')
        self.sta.active(True)
        connected = False
        if self.sta.isconnected():
            logging.info('Connected: %s', self.sta.ifconfig())
            return True
        self.sta_connecting = True
        for credentials in self.ssids:
            ssid = credentials[1]
            password = credentials[2]
            connected = await self.connect_to(ssid, password)
            if connected:
                logging.info('Connected to %s %s', ssid, self.sta.ifconfig())
                log_serverUrl()
                return connected
            else:
                logging.info('Failed to connect to ' + ssid)
        logging.debug('No Wi-FI connection made')
        self.sta_connecting = False
        return connected

    async def connect_to(self, ssid, password):
        logging.debug('Trying to connect to %s...' % ssid)
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
        logging.debug('Scanning for Wi-Fi networks')
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
        if len(self.ssids) > WIFI_MAX_SSIDS:
            logging.debug('too many ssids - pop the last')
            wifi_manager.ssids.pop(WIFI_MAX_SSIDS)


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
        logging.debug('run_wap_loop')
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
        logging.info('AP active - SSID:' + ssid + ' password:' + password + ' IP:' + str(self.ap.ifconfig()[0]))

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


@server.route("/settings", methods=["GET"])
@server.route("/settings/", methods=["GET"])
@server.route("/settings/wifi", methods=["GET"])
@server.route("/settings/wifi/", methods=["GET"])
async def home(request):
    logging.debug("/wifi/home")
    args = get_args(page='Wi-Fi Home')
    return await render_template(f"{WIFI_TEMPLATE_PATH}/home.html", args=args)


@server.route('/settings/wifi/configure_wifi', methods=['GET', 'POST'])
async def configure_wifi(req):
    logging.debug("/wifi/configure")
    args = get_args(page='Configure Wi-Fi')
    args['waps'] = wifi_manager.scan_for_waps_sorted()
    return await render_template(f"{WIFI_TEMPLATE_PATH}/configure_wifi.html", args=args)


@server.route('/settings/wifi/add_ssid', methods=['GET', 'POST'])
async def add_ssid(req):
    logging.debug('add_ssid')
    form = req.form
    action = form['action']
    if 'Add' == action:
        new_ssid = form['ssid']
        logging.debug('add_ssid ' + new_ssid)
        new_password = form['password']
        wifi_manager.insert_ssid(new_ssid, new_password)
    args = get_args(page='Add SSID', form=form)
    args['waps'] = wifi_manager.scan_for_waps_sorted()
    return await render_template(f"{WIFI_TEMPLATE_PATH}/configure_wifi.html", args=args)


@server.route('/settings/wifi/update_ssid', methods=['GET', 'POST'])
async def update_ssid(req):
    logging.debug('update_ssid')
    form = req.form
    ssid_index = form['ssid_index']
    try:
        index = int(ssid_index)
        action = form['action']
        logging.debug('' + action + ' ' + str(index))
        if 'Remove' == action:
            logging.debug('update_ssid removing ssid ' + str(index))
            wifi_manager.ssids.pop(index)
        if 'v' == action:
            logging.debug('update_ssid ssid down ' + str(index))
            wifi_manager.move_ssid_to(index, index + 1)
        if '^' == action:
            logging.debug('update_ssid ssid up ' + str(index))
            wifi_manager.move_ssid_to(index, index - 1)
        if 'Update' == action:
            logging.debug('update_ssid password ' + str(index))
            new_password = form['password']
            wifi_manager.ssids[index][2] = new_password

    except ValueError:
        logging.error('update ssid invalid value' + ssid_index)
    except IndexError:
        logging.error('update ssid curr_index out of range' + ssid_index)
    args = get_args(page='Remove SSID', form=form)
    args['waps'] = wifi_manager.scan_for_waps_sorted()
    return await render_template(f"{WIFI_TEMPLATE_PATH}/configure_wifi.html", args=args)


@server.route('/settings/wifi/update_config', methods=['GET', 'POST'])
async def update_config(req):
    logging.debug('update_config ')
    form = req.form
    action = form['action']
    if 'Reload' == action:
        logging.debug('update_config Reload')
        wifi_manager.load()
    if 'Save' == action:
        logging.debug('update_config Save')
        wifi_manager.save()
    args = get_args(page='Configure Wi-Fi')
    args['waps'] = wifi_manager.scan_for_waps_sorted()
    return render_template(f"{WIFI_TEMPLATE_PATH}/configure_wifi.html", args=args)


def log_serverUrl():
    ssl = None
    port = 80
    if ssl is None:
        if port == 80:
            logging.info('http://' + wifi_manager.get_host())
        else:
            logging.info('http://' + wifi_manager.get_host() + ':' + str(port))
    else:
        if port == 443:
            logging.info('https://' + wifi_manager.get_host())
        else:
            logging.info('http://' + wifi_manager.get_host() + ':' + str(port))


def get_args(page, form=None):
    wifi_sta = 'Not connected'
    wifi_sta_connected = wifi_manager.sta.isconnected()
    if wifi_sta_connected:
        wifi_sta = wifi_manager.sta.config('ssid')
    wifi_ap = wifi_manager.wlan_attributes["HOSTNAME"]
    wifi_ap_password = wifi_manager.wlan_attributes["PASSWORD"]
    wifi_ap_connected = wifi_manager.ap.isconnected()
    wifi_ap_up = wifi_manager.ap.active()

    ifconfig = wifi_manager.sta.ifconfig()
    ssids = wifi_manager.ssids
    args = {'app_name': APP_NAME,
            'page': page,
            'wifi_sta': wifi_sta,
            'wifi_sta_connected': wifi_sta_connected,
            'wifi_ap': wifi_ap,
            'wifi_ap_status' : ['down', 'up'][wifi_ap_up],
            'wifi_ap_password': wifi_ap_password,
            'wifi_ap_connected': wifi_ap_connected,
            'wifi_ap_required': wifi_manager.wlan_attributes["RUNWAP"],
            'wifi_ap_choices': wifi_manager.wlan_attributes["RUNWAP_CHOICES"],
            'ifconfig': ifconfig,
            'ssids': ssids,
            'form': form}
    return args
