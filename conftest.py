import pytest
import json
import time
import os
import re
import requests
from requests.auth import HTTPBasicAuth
from pytest_cases import fixture
from objectpath import Tree
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

active_service = []  # A list of SMARTBOX services which are active
all_logos = []  # For storing all the JSON files of the logos
in_use_logos = []  # Create a list of the the logos in the OnStream guide
guide_uid = []  # A list of the OnStream UID's from the guide
guide_images = []  # A list of the OnStream image URLs from the guide
all_ld = []  # A list of the JSON files that are in-use


def pytest_addoption(parser):
    parser.addoption("--onstream_url", dest="onstream_url", action="store", default="https://test.watchdishtv.com/", help="The URL for the OnStream instance you wish to test")
    parser.addoption("--smartbox_ip", dest="smartbox_ip", action="store", default="https://10.11.46.146", help="The IP of the SMARTBOX which has the channel lineup for the Onstream instance you are testing with")  #Changed IP to because of Gen2
    parser.addoption("--onstream_version", dest="onstream_version", action="store", default="1.2.32", help="The OnStream version you will be testing")
    parser.addoption("--channel_loop", dest="channel_loop", action="store", default="40", help="The number of channels you wish to flip through in OnStream")
    parser.addoption("--grafana_ip", dest="grafana_ip", action="store", default="10.11.46.179", help="The IP of the Grafana instance")
    parser.addoption("--grafana_port", dest="grafana_port", action="store", default="8086", help="The IP of the Grafana instance")
    parser.addoption("--custom_logo", dest="custom_logo", action="store", default="Infio Whites", help="The Custom Logo which appears in the middle of the main page for OnStream")  #Changed the custom logo

@pytest.fixture(scope="session")
def onstream_url(request):
    return request.config.getoption("--onstream_url")


@pytest.fixture(scope="session")
def smartbox_ip(request):
    return request.config.getoption("--smartbox_ip")


@pytest.fixture(scope="session")
def onstream_version(request):
    return request.config.getoption("--onstream_version")


@pytest.fixture(scope="session")
def channel_loop(request):
    return request.config.getoption("--channel_loop")


@pytest.fixture(scope="session")
def grafana_ip(request):
    return request.config.getoption("--grafana_ip")


@pytest.fixture(scope="session")
def grafana_port(request):
    return request.config.getoption("--grafana_port")


@pytest.fixture(scope="session")
def custom_logo(request):
    return request.config.getoption("--custom_logo")


@pytest.fixture(scope="session", autouse=True)
def smartbox_setup(request, smartbox_ip):
    
    url = smartbox_ip + "/web/analytics/streaminfo"
    response = requests.get(url,
                            auth=HTTPBasicAuth('username', 'password'), verify=False,
                            headers={'User-Agent': 'Custom'})

    # print(response)
    out_json = response.json()
    data = out_json['data']['services']
    info = {}
    for services in data:
        temp_list = [services['serviceId']]
        temp_list.append(services['overallState']['color'])
        info[services['serviceName']] = temp_list
    for key, value in info.items():
        if value[1] == 'OK':
            kv = key, value
            active_service.append(kv)
    return active_service


@fixture(unpack_into="all_channels,first_channel,all_guide_uid,all_guide_images,call_letters", scope="session", autouse=True)
def channel_count(request, onstream_url):
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--start-maximized')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--ignore-certificate-errors')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    dishtv = onstream_url
    driver.get(dishtv)
    WebDriverWait(driver, 30).until(ec.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/div[2]/span/span[2]/a/span'))).click()  # Click on the TV Guide Button
    WebDriverWait(driver, 30).until_not(ec.visibility_of_element_located((By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')))  # Wait for the loading screen to disappear
    WebDriverWait(driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[2]/div/div/div/div[1]/div[1]')))  # Wait for the TODAY text to appear
    time.sleep(3)
    links = []
    channels = driver.find_elements(By.XPATH, '//a[@class="_2eB_OXy4vbP1Kd9moNzO4j"]')  # Get the Video Player Classes
    for i in range(len(channels)):
        links.append(channels[i].get_attribute("href"))  # create a dict of the channel links
    all_channels = list(dict.fromkeys(links))  # update the dict into a list from the keys
    first_channel = all_channels[0].split('/')[5]  # extract only the necessary URL link
    logos = driver.find_elements(By.XPATH, '//img[@class="_2taHIt9ptBC9h3nyExFgez"]')  # Channel Logos
    for i in range(len(logos)):  # A for loop that collects certain information from the OnStream guide which will be validated against the JSON information
        guide_uid.append(logos[i].get_attribute("alt"))
        guide_images.append(logos[i].get_attribute('src'))
    all_guide_uid = list(dict.fromkeys(guide_uid))
    all_guide_images = list(dict.fromkeys(guide_images))
    driver.quit()

    for subdir, dirs, files in os.walk(os.path.abspath(os.curdir + os.sep + 'logos' + os.sep)):  # A for loop which goes through the logos folder and collects the necessary data for future parsing
        files = [f for f in files if not f[0] == '.']
        dirs[:] = [d for d in dirs if not d[0] == '.']
        for file in files:
            filepath = subdir + os.sep + file
            all_logos.append(filepath)

    for x in range(len(all_channels)):  # A for loop which goes through the list of channels in the OnStream guide and compares with the list of the JSON files from the above for loop, to create one list with only in-use items
        c = all_channels[x].split('/')[5]
        regex = re.compile('.*(channel_logo_info_%s).json' % c)
        select = filter(regex.match, all_logos)
        for s in select:
            in_use_logos.append(s)

    for js in in_use_logos:  # Take the JSON data from the above for loop and delete un-needed information and create a new list
        with open(js) as json_file:
            ld = json.load(json_file)
            del ld['is_hd']
            del ld['service_type']
            all_ld.append(ld)

    for logo in all_ld:  # A for loop to confirm the call_letters for the first channel in the Guide
        if str(logo['suid']) == first_channel:
            call_letters = logo['callsign']
    return all_channels, first_channel, all_guide_uid, all_guide_images, call_letters
