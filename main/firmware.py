import logging
from phew import server
from phew.template import render_template

from settings import SETTINGS_TEMPLATE_PATH, APP_NAME


@server.route("/settings/firmware", methods=["GET"])
@server.route("/settings/firmware/", methods=["GET"])
async def wifi_home(request):
    logging.debug("firmware_home")
    args = get_args(page='Firmware Home')
    return await render_template(f"{SETTINGS_TEMPLATE_PATH}/firmware_home.html", args=args)


@server.route("/settings/firmware/configure", methods=["GET"])
async def wifi_home(request):
    logging.debug("firmware_home")
    args = get_args(page='Firmware Home')
    return await render_template(f"{SETTINGS_TEMPLATE_PATH}/firmware_configure.html", args=args)


def get_args(page, form=None):
    args = {'app_name': APP_NAME,
            'page': page,
            'form': form}
    return args
