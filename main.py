import sys
import micropython_ota
import network
import socket
import requests
import time

wlan_sta = network.WLAN(network.STA_IF)

def do_connect(ssid='jamnethome_2GHz', password='pa55word90123!'):
    print('do_connect()')
    connected = None
    wlan_sta.active(True)
    if wlan_sta.isconnected():
        print('Connected: ', wlan_sta.ifconfig())
        return None
    print('Trying to connect to %s...' % ssid)
    wlan_sta.connect(ssid, password)
    for retry in range(100):
        connected = wlan_sta.isconnected()
        if connected:
            break
        time.sleep(0.1)
        print('.', end='')
    if connected:
        print('\nConnected: ', wlan_sta.ifconfig())
    else:
        print('\nFailed. Not Connected to: ' + ssid)
    return connected

def disconnect_wifi():
    wlan_sta.active(True)
    if not wlan_sta.isconnected():
        return None
    wlan_sta.disconnect()


def http_get(host='', path=''):

    url='https://1drv.ms/t/s!AgUtKRuWyBCtloRNgOC4MIRUXVGVAQ?e=IzeAwW'
    url='https://drive.google.com/file/d/14rSq2J_wrDV_qIotLTCFt5TPppJ2iQHk/view?usp=drive_link'
    #url='https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd'
    path='/OTA'

    print(url)
    response = requests.get(url)
    # Get response code
    response_code = response.status_code
    print(response_code)
    # Get response content
    response_content = response.content
    print(response_content)


def connect_wifi():
    print('connect_wifi()')
    do_connect()

def main():
    # connect_wifi()
    pass

if __name__ == '__main__':
    main()