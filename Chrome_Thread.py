import os
import subprocess
from threading import Thread
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

try:
    base_path = os.environ['ONSTREAM_HOME']
except KeyError:
    print('Could not get environment variable "base_path". This is needed for the tests!"')
    raise
try:
    test_path = os.environ['ONSTREAM_TEST']
except KeyError:
    print('Could not get environment variable "test_path". This is needed for the tests!"')
    raise
version = '1.2.27'


class ChannelCount(object):
    caps = DesiredCapabilities.CHROME
    caps['goog:loggingPrefs'] = {'performance': 'ALL'}
    driver = webdriver.Chrome(ChromeDriverManager().install(), desired_capabilities=caps)
    dishtv = "https://watchdishtv.com/"
    driver.get(dishtv)
    WebDriverWait(driver, 30).until(ec.presence_of_element_located((By.XPATH, '//button[@class="_2YXx31Mkp4UfixOG740yi7 schema_accent_background"]'))).click()
    WebDriverWait(driver, 30).until_not(ec.visibility_of_element_located((By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')))
    WebDriverWait(driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="9491"]')))
    links = []
    channels = driver.find_elements_by_xpath('(//a[@class="_2GEDK4s6kna2Yfl6_0Q6c_"])')
    for i in range(len(channels)):
        links.append(channels[i].get_attribute("href"))
    all_channels = list(dict.fromkeys(links))
    driver.quit()


class CountRun:
    def __init__(self):
        self.counter = 0
        self.line = 0

    def increment(self):
        self.counter += 1

    def reset(self):
        self.counter = 0

    def get_value(self):
        with open(os.path.join(base_path, 'test_run_num.txt'), 'r') as rt:
            self.line = str(rt.read())
        return self.line

    def save_value(self):
        with open(os.path.join(base_path, 'test_run_num.txt'), 'w+') as tr:
            tr.write(str(self.counter))


class ChannelChange:
    def __init__(self):
        self.change = 1000

    def get_number(self):
        return self.change


mc = CountRun()
cc = ChannelChange()


def pytest_run():
    channels = ChannelCount.all_channels
    while int(len(channels)) < int(cc.get_number()):
        mc.increment()
        mc.save_value()
        subprocess.run(['pytest', '--pytest-influxdb', '--influxdb_project=Chrome', '--influxdb_run_id=' + str(mc.get_value()), os.path.join(test_path, 'OnStream_Chrome.py'), '-sv'])
        channels = ChannelCount.all_channels + channels


if __name__ == "__main__":
    t1 = Thread(target=pytest_run)
    t1.start()
    t1.join()
