import os
import subprocess
import pytest
import json
import time
from appium import webdriver
from selenium.webdriver import ActionChains
from appium.webdriver.appium_service import AppiumService
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from influxdb import InfluxDBClient

version = '1.2.27'

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
try:
    picture_path = os.environ['ONSTREAM_PICTURES']
except KeyError:
    print('Could not get environment variable "test_path". This is needed for the tests!"')
    raise
try:
    grafana = os.environ['GRAFANA']
except KeyError:
    print('Could not get environment variable "grafana". This is needed for the tests!"')
    raise

client = InfluxDBClient(host=grafana, port=8086, database='ONSTREAM')


@pytest.fixture(scope="class")
def directory(request):
    name = os.environ.get('PYTEST_CURRENT_TEST')
    direct = '/Users/dishbusiness/Desktop/OnStreamTestFiles/Pictures/'
    request.cls.direct = direct
    request.cls.name = name
    yield


@pytest.fixture(scope="class")
def setup(request):
    appium_service = AppiumService()
    appium_service.start()
    desired_caps = {}
    desired_caps['xcodeOrgId'] = 'QPWT4523KW'
    desired_caps['xcodeSigningId'] = 'iPhone Developer'
    desired_caps['platformName'] = 'iOS'
    desired_caps['deviceName'] = 'iPhone 8'
    desired_caps['automationName'] = 'XCUITest'
    desired_caps['platformVersion'] = '14.3'
    desired_caps['browserName'] = 'Safari'
    desired_caps['udid'] = '010c4b573b786d85098a89de6e1b47b79d612d14'
    desired_caps['showXcodeLog'] = True
    desired_caps['updatedWDABundleId'] = 'com.test.OnStream'
    driver = webdriver.Remote('http://localhost:4723/wd/hub', desired_caps)
    driver.get('https://watchdishtv.com/')
    request.cls.driver = driver
    yield
    driver.quit()


@pytest.mark.usefixtures("setup", "directory")
class TestVersion:
    def test_version(self):
        WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//button[@class="_1ATKIs2nHrPvAu0b3sAXQz"]'))).click()
        WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//span[contains(text(), "Settings")]'))).click()
        WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//li[@class="_1c_-iIVNzHdk3aepkUNNWh schema_accent_border-bottom"]')))
        v = self.driver.find_element(By.XPATH, '//p[@class="_2G-12UYHfG0a2MlL0pEXtD"]')
        v = v.text.split(':')[1].strip()
        assert version == v

