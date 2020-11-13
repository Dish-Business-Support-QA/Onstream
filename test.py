import os
import csv
import pytest
import json
import time
import glob
import re
import pandas as pd
import numpy as np
import linecache
import time
import subprocess
from collections import Counter
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Thread
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException, JavascriptException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.opera import OperaDriverManager
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import pychromecast
from pandas.errors import EmptyDataError


@pytest.fixture(scope="class")
def directory(request):
    name = os.environ.get('PYTEST_CURRENT_TEST')
    """.split(':')[-1].split(' ')[0]"""
    direct = '/Users/dishbusiness/Desktop/OnStreamTestFiles/Pictures/'
    request.cls.direct = direct
    request.cls.name = name
    yield


@pytest.fixture(scope="class")
def setup(request):
    caps = DesiredCapabilities.CHROME
    caps['goog:loggingPrefs'] = {'performance': 'ALL'}
    driver = webdriver.Chrome(ChromeDriverManager().install(), desired_capabilities=caps)
    dishtv = "https://test.watchdishtv.com/"
    driver.get(dishtv)
    driver.maximize_window()
    logo = "DaVita Logo"  # Big logo on home screen
    src = driver.page_source
    request.cls.driver = driver
    request.cls.src = src
    request.cls.dishtv = dishtv
    request.cls.logo = logo
    yield
    driver.quit()


@pytest.fixture(scope="class")
def now_time(request):
    t1 = datetime.now() + timedelta(hours=1)
    t2 = datetime.now() + timedelta(hours=2)
    t3 = datetime.now() + timedelta(hours=3)

    if datetime.now().strftime('%M') < str(30):
        m = str("{0:0>2}".format(0))
    elif datetime.now().strftime('%M') > str(30):
        m = str(30)
    now = datetime.now().strftime('%-I:' + m)
    now1 = t1.strftime('%-I:' + m)
    now2 = t2.strftime('%-I:' + m)
    now3 = t3.strftime('%-I:' + m)
    request.cls.now = now
    request.cls.now1 = now1
    request.cls.now2 = now2
    request.cls.now3 = now3
    yield


@pytest.mark.usefixtures("setup", "directory", "now_time")
class TestLiveTV:
    def test_images_displayed(self):
        WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
            (By.XPATH, '//button[@class="_2YXx31Mkp4UfixOG740yi7 schema_accent_background"]'))).click()
        WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located(
            (By.XPATH, '//img[@alt="9487"]')))
        try:
            if ":" + str(30) in self.now:
                try:
                    service = WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located(
                        (By.XPATH, '(//a[@href="#/player/9487"])[1]')))  # go to the play button
                    ActionChains(self.driver).move_to_element(service).perform()  # hover mouse over it
                    ActionChains(self.driver).click(service).perform()  # click on the service
                except JavascriptException:
                    service = WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located(
                        (By.XPATH, '(//a[@href="#/player/9487"])[2]')))  # go to the play button
                    ActionChains(self.driver).move_to_element(service).perform()  # hover mouse over it
                    ActionChains(self.driver).click(service).perform()  # click on the service
                    pass
            else:
                service = WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located(
                    (By.XPATH, '(//a[@href="#/player/9487"])[2]')))  # go to the play button
                ActionChains(self.driver).move_to_element(service).perform()  # hover mouse over it
                ActionChains(self.driver).click(service).perform()  # click on the service

            WebDriverWait(self.driver, 30).until_not(ec.presence_of_element_located(
                (By.XPATH,
                 '//div[@class="nvI2gN1AMYiKwYvKEdfIc '
                 'schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')))
            # wait for loading screen to disappear
        except NoSuchElementException as e:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            raise Exception("Element could not be found! Please view the Screenshot!") from e
        except TimeoutException as t:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            raise Exception("The test timed out! Please view the Screenshot!") from t
