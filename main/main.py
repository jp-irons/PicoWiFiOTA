# import micropython_ota
import os
import logging
import uasyncio as asyncio
from phew import server
from phew.template import render_template
import settings
import firmware
import wifimanager

LOG_LEVEL = logging.LOG_ALL

logging._logging_types = LOG_LEVEL


async def start_server(host="0.0.0.0", port=80):
    logging.debug('start server')
    server.run(host, port)


async def run_app():
    logging.debug('starting app')
    port = 80
    await asyncio.gather(
        wifimanager.wifi_manager.setup_connection(),
        wifimanager.wifi_manager.run_wap_loop(),
        start_server(port=port)
    )
    logging.debug('app finished')


def disconnect_wifi():
    wifimanager.wifi_manager.sta.active(True)
    if not wifimanager.wifi_manager.sta.isconnected():
        return None
    wifimanager.wifi_manager.sta.disconnect()


def execute():
    asyncio.run(run_app())


def debug():
    logging._logging_types = logging.LOG_ALL
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
