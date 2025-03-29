# import micropython_ota
import os

import logging
import uasyncio as asyncio
from phew import server
from phew.template import render_template
import settings
import firmware
import wifimanager
from tarfile import TarFile

LOG_LEVEL = logging.LOG_ALL

logging._logging_types = LOG_LEVEL

def exists(path):
    try:
        _ = os.stat(path)
    except:
        return False
    else:
        return True


def untar(tarfilename, target='/untar', overwrite=False, verbose=False, chunksize=4096):
    size_b, free_b = print_memory('before')
    with open(tarfilename) as tar:
        if not exists(target):
            print(target)
            os.mkdir(target)
        for info in TarFile(fileobj=tar):
            print(info.name)
            if info.type == "dir":
                if verbose:
                    print("D %s" % info.name)

                name = target + '/' + info.name.rstrip("/")
                if not exists(name):
                    print(name)
                    os.mkdir(name)
            elif info.type == "file":
                if verbose:
                    print("F %s" % info.name)

                if overwrite or not exists(info.name):
                    with open(info.name, "wb") as fp:
                        while True:
                            chunk = info.subf.read(chunksize)
                            if not chunk:
                               break
                            fp.write(chunk)
            elif verbose:
                print("? %s" % info.name)
    size_a, free_a = print_memory('after')
    print('used:  ', free_b-free_a)

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


def memory(note=''):
    stat = os.statvfs("/")
    size = stat[1] * stat[2]
    free = stat[0] * stat[3]
    return size, free

def print_memory(note=''):
    print('memory', note)
    size, free = memory()
    print('flash: ', size)
    print('free:  ', free)
    return size, free


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
