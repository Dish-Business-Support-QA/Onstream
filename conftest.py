import pytest
import os
import time
from influxdb import InfluxDBClient
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

try:
    grafana = os.environ['GRAFANA']
except KeyError:
    print('Could not get environment variable "grafana". This is needed for the tests!"')
    raise
client = InfluxDBClient(host=grafana, port=8086, database='ONSTREAM')


@pytest.fixture(scope="session", autouse=True)
def auto_start(request):
    from Chrome_Thread import version, test_run
    test_start = [
        {
            "measurement": "Chrome",
            "tags": {
                "Software": version,
            },
            "time": time.time_ns(),
            "fields": {
                "events_title": "test start",
                "text": "This is the start of test " + str(test_run) + " on firmware " + version,
                "tags": "Onstream" + "," + "Chrome" + "," + str(test_run) + "," + version
            }
        }
    ]
    client.write_points(test_start)

    def auto_fin():
        test_end = [
            {
                "measurement": "Chrome",
                "tags": {
                    "Software": version,
                },
                "time": time.time_ns(),
                "fields": {
                    "events_title": "test end",
                    "text": "This is the end of test " + str(test_run) + " on firmware " + version,
                    "tags": "Onstream" + "," + "Chrome" + "," + str(test_run) + "," + version
                }
            }
        ]
        client.write_points(test_end)

    request.addfinalizer(auto_fin)
