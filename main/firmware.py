import json
import network
import uasyncio as asyncio

import logging
from main import APP_NAME
from phew import server
from phew.template import render_template

SETTINGS_TEMPLATE_PATH = "content/settings"

@server.route("/settings", methods=["GET"])
@server.route("/settings/", methods=["GET"])
async def settings_home(request):
    logging.debug("settings_home")
    args = get_args(page='Settings Home')
    return await render_template(f"{SETTINGS_TEMPLATE_PATH}/home.html", args=args)


@server.route("/settings/firmware", methods=["GET"])
@server.route("/settings/firmware/", methods=["GET"])
async def wifi_home(request):
    logging.debug("firmware_home")
    args = get_args(page='Firmware Home')
    return await render_template(f"{SETTINGS_TEMPLATE_PATH}/firmware.html", args=args)


def get_args(page, form=None):
    args = {'app_name': APP_NAME,
            'page': page,
            'form': form}
    return args
