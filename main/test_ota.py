from ota import ota_manager
from uaiohttpclient import request
import requests

def test_ota():
    print('test_ota()')
    pass

def print_url(url='https://github.com/jp-irons/PicoWiFiOTA/raw/refs/heads/ota/releases/versions.json'):
    print('url ', url)
    source = requests.get(url)
    content = source.json()
    print(content)

import requests
import ujson as json
response = requests.get("https://raw.githubusercontent.com/jp-irons/PicoWiFiOTA/refs/heads/ota/releases/versions.json")
# Get response code
response_code = response.status_code
# Get response content
content = response.content
attributes = json.loads(content)


# Print results
print('Response code: ', response_code)
print('Response content:', content)
