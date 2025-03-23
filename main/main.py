# import micropython_ota
import os
import logging
# import asyncio
import uasyncio as asyncio
from phew import server
from phew.template import render_template
import wifimanager


# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)
#
APP_NAME = "Pi Pico Embedded"
AP_DOMAIN = "pipico.net"

CONTENT_PATH = "content"
IMAGES_PATH = "content/static"
APP_TEMPLATE_PATH = "content/app"

LOG_LEVEL = logging.LOG_ALL

logging._logging_types = LOG_LEVEL


#app_name = "Pi Pico Embedded"
# return file in IMAGES_PATH
@server.route("/static/<file_name>", methods=['GET', 'POST'])
async def static(request, file_name):
    file_path = f"{IMAGES_PATH}/{file_name}"
    logging.debug('getting static content ' + file_path)
    page = open(file_path, "rb")
    content = page.read()
    page.close()
    return content, 200



# @server.route('/', methods=['GET', 'POST'])
# async def curr_index(req):
#     return Template('home.html').render(page='Index')
#
#

# catchall example
@server.catchall()
async def catchall(request):
    args = wifimanager.get_args(page='Not found error: 404')
    args['url'] = request.uri
    return await render_template(f"{CONTENT_PATH}/unexpected.html", args=args), 404


# url parameter and template render
@server.route("/", methods=["GET"])
async def home(request):
    args = wifimanager.get_args(page='Home')
    return await render_template(f"{CONTENT_PATH}/home.html", args=args)


# @server.route('/page2')
# async def page2(req):
#     args = get_args(page='Page 2')
#     return Template('page2.html').render(args)


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
