import os
import subprocess
import platform
import json
import time
import re
from threading import Thread
from objectpath import Tree
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from argument_onstream import args

browser = os.path.basename(__file__).split("_")[0]
plat = platform.platform().split('-')
device = str(plat[0] + "-" + plat[1])
version = args.onstream_version
all_logos = []  # For storing all the JSON files of the logos
in_use_logos = []  # Create a list of the the logos in the OnStream guide
guide_uid = []  # A list of the OnStream UID's from the guide
guide_images = []  # A list of the OnStream image URLs from the guide
all_ld = []  # A list of the JSON files that are in-use
active_service = []  # A list of SMARTBOX services which are active


class SmartboxData(object):
    optionsforchrome = Options()
    optionsforchrome.add_argument('--no-sandbox')
    optionsforchrome.add_argument('--start-maximized')
    optionsforchrome.add_argument('--disable-extensions')
    optionsforchrome.add_argument('--disable-dev-shm-usage')
    optionsforchrome.add_argument('--ignore-certificate-errors')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=optionsforchrome)
    SMARTBOX = args.smartbox_ip
    driver.get(SMARTBOX)
    driver.maximize_window()
    driver.find_element(By.NAME, "username").click()
    driver.find_element(By.NAME, "username").send_keys("username")
    driver.find_element(By.NAME, "password").click()
    driver.find_element(By.NAME, "password").send_keys("password")
    driver.find_element(By.XPATH, "//input[@value=\'Login\']").click()
    time.sleep(5)
    fieldnames = ['Time']
    driver.get(args.smartbox_ip + "/getanalytics.php")
    result = json.loads(driver.find_element(By.TAG_NAME, 'body').text)
    result_tree = Tree(result)
    service_name_path = "$.webFullStreamInfo.service.serviceName"
    service_name = result_tree.execute(service_name_path)
    service_identifier_path = "$.webFullStreamInfo.service.serviceIdentifier"
    service_identifier = result_tree.execute(service_identifier_path)
    service_state_path = "$.webFullStreamInfo.service.state"
    service_state = result_tree.execute(service_state_path)
    service_name_list = list(service_name)
    service_identifier_list = list(service_identifier)
    service_state_list = list(service_state)
    d = {z[0]: list(z[1:]) for z in zip(service_name_list, service_identifier_list, service_state_list)}
    for key, value in d.items():
        if value[1] == 'Service is active':
            kv = key, value
            active_service.append(kv)
    driver.quit()


class ChannelCount:
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--start-maximized')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--ignore-certificate-errors')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    dishtv = args.onstream_url
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


class CountRun:
    def __init__(self):
        self.counter = 0
        self.line = 0

    def increment(self):
        self.counter += 1

    def reset(self):
        self.counter = 0

    def get_value(self):
        with open(os.path.abspath(os.curdir + os.sep + 'test_run_num.txt'), 'r') as rt:
            self.line = str(rt.read())
        return self.line

    def save_value(self):
        with open(os.path.abspath(os.curdir + os.sep + 'test_run_num.txt'), 'w+') as tr:
            tr.write(str(self.counter))


class ChannelChange:
    def __init__(self):
        self.change = args.channel_loop

    def get_number(self):
        return self.change


mc = CountRun()
cc = ChannelChange()


def pytest_run():
    channels = ChannelCount.all_channels
    while int(len(channels)) < int(cc.get_number()):
        mc.increment()
        mc.save_value()
        subprocess.call(['pytest', '--pytest-influxdb', '--influxdb_project=Chrome', '--influxdb_run_id=' + str(mc.get_value()), '--influxdb_version=' + str(version), os.path.abspath(os.curdir + os.sep + 'OnStream_Chrome.py'), '-sv'])
        channels = ChannelCount.all_channels + channels


if __name__ == "__main__":
    t1 = Thread(target=pytest_run)
    t1.start()
    t1.join()
