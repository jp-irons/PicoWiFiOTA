import logging
from phew import server
from phew.template import render_template

APP_NAME = "Pi Pico Embedded"
AP_DOMAIN = "pipico.net"

SETTINGS_TEMPLATE_PATH = "content/settings"
CONTENT_PATH = "content"
IMAGES_PATH = "content/static"
APP_TEMPLATE_PATH = "content/app"


# url parameter and template render
@server.route("/", methods=["GET"])
async def home(request):
    args = get_args(page='Home')
    return await render_template(f"{CONTENT_PATH}/home.html", args=args)


# @server.route('/page2')
# async def page2(req):
#     args = get_args(page='Page 2')
#     return Template('page2.html').render(args)

@server.route("/settings", methods=["GET"])
@server.route("/settings/", methods=["GET"])
async def settings_home(request):
    logging.debug("settings_home")
    args = get_args(page='Settings')
    return await render_template(f"{SETTINGS_TEMPLATE_PATH}/home.html", args=args)


# return file in IMAGES_PATH
@server.route("/static/<file_name>", methods=['GET', 'POST'])
async def static(request, file_name):
    file_path = f"{IMAGES_PATH}/{file_name}"
    logging.debug('getting static content ' + file_path)
    page = open(file_path, "rb")
    content = page.read()
    page.close()
    return content, 200


# catchall example
@server.catchall()
async def catchall(request):
    args = get_args(page='Not found error: 404')
    args['url'] = request.uri
    return await render_template(f"{CONTENT_PATH}/unexpected.html", args=args), 404

def get_args(page, form=None):
    args = {'app_name': APP_NAME,
            'page': page,
            'form': form}
    return args
