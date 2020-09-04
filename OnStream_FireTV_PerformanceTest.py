#! /usr/bin/env monkeyrunner

import os
import time
import subprocess
import pytest
import pandas as pd
import matplotlib.pyplot as plt
import json
from datetime import datetime
from datetime import timedelta
from appium import webdriver
from appium.webdriver.appium_service import AppiumService
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from CountServices import services

version = '1.0.0'
test = 'test1'


def setup_module(module):
    subprocess.call(['python3', 'OnStreamClearFolders.py'])
    return module


@pytest.fixture(scope="session")
def count_services():
    subprocess.call(['python3', 'CountServices.py'])
    yield


@pytest.fixture(scope="class")
def setup(request):
    subprocess.call(['adb', 'shell', 'input', 'keyevent', 'KEYCODE_HOME'])
    appium_service = AppiumService()
    appium_service.start()
    desired_caps = {}
    desired_caps['platformName'] = 'Android'
    desired_caps['deviceName'] = 'raven'
    desired_caps['automationName'] = 'UiAutomator2'
    desired_caps['udid'] = '172.19.5.96:5555'
    desired_caps['platformVersion'] = '7.0'
    desired_caps['appPackage'] = 'tv.accedo.xdk.dishtv'
    desired_caps['appActivity'] = 'MainActivity'
    desired_caps['eventTimings'] = 'True'
    desired_caps['recordDeviceVitals'] = 'True'
    driver = webdriver.Remote('http://localhost:4723/wd/hub', desired_caps)
    request.cls.driver = driver
    yield
    time_events = driver.get_events()
    with open('/Users/dishbusiness/Desktop/OnStreamTestFiles/Duration/Event_Time_Log.json', 'w', encoding='utf-8') as t:
        json.dump(time_events, t, ensure_ascii=False, indent=4)
    gfx = open('/Users/dishbusiness/Desktop/OnStreamTestFiles/Logs/GFX_Log.txt', "w", encoding='ISO-8859-1')
    subprocess.run(['adb', 'shell', 'dumpsys', 'gfxinfo', 'tv.accedo.xdk.dishtv', 'framestats'], stdout=gfx)
    time.sleep(30)
    with open('/Users/dishbusiness/Desktop/OnStreamTestFiles/Logs/GFX_Log.txt', encoding='ISO-8859-1') as infile, \
            open('/Users/dishbusiness/Desktop/OnStreamTestFiles/Logs/OnStream_GFX_Stream.csv', 'w') as outfile:
        copy = False
        for line in infile:
            if line.strip() == "---PROFILEDATA---":
                copy = True
                continue
            elif line.strip() == "View hierarchy:":
                copy = False
                continue
            elif copy:
                outfile.write(line)
    df = pd.read_csv(r'/Users/dishbusiness/Desktop/OnStreamTestFiles/Logs/OnStream_GFX_Stream.csv')
    flag = df.loc[df['Flags'] == 0]
    mill = flag.div(10000000)
    fld = (mill["FrameCompleted"] - mill["IntendedVsync"])
    p = fld.plot()
    p.axhline(y=16, linewidth=2, color='r')
    plt.savefig('/Users/dishbusiness/Desktop/OnStreamTestFiles/Pictures/gfx_OnStream.png')
    plt.clf()
    cpu = driver.get_performance_data('tv.accedo.xdk.dishtv', 'memoryinfo', 10)
    with open('/Users/dishbusiness/Desktop/OnStreamTestFiles/Duration/cpu.txt', 'w', encoding='ISO-8859-1') as c:
        print(cpu, file=c)
    driver.quit()


@pytest.fixture(scope="class")
def directory(request):
    name = os.environ.get('PYTEST_CURRENT_TEST').split(':')[-1].split(' ')[0]
    direct = '/Users/dishbusiness/Desktop/OnStreamTestFiles/Pictures/'
    request.cls.direct = direct
    request.cls.name = name
    yield


@pytest.mark.usefixtures("setup", "directory")
class TestHomeScreen:
    def test_popular_channels(self):
        WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
            (By.XPATH, "//android.view.View[contains(@text, 'VIEW FULL TV GUIDE')]")))
        live1 = self.driver.find_element_by_xpath("//android.view.View[contains(@bounds, '[192,805][672,886]')]")
        live2 = self.driver.find_element_by_xpath("//android.view.View[contains(@bounds, '[720,805][1200,886]')]")
        live3 = self.driver.find_element_by_xpath("//android.view.View[contains(@bounds, '[1248,805][1728,886]')]")
        live = [live1, live2, live3]
        for x in live:
            try:
                x.click()
                time.sleep(5)
                self.driver.press_keycode(4)
                WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                    (By.XPATH, "//android.view.View[contains(@text, 'TODAY')]")))
                self.driver.press_keycode(4)
                WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                    (By.XPATH, "//android.view.View[contains(@text, 'VIEW FULL TV GUIDE')]")))
                continue
            except NoSuchElementException as e:
                self.driver.save_screenshot(self.direct + self.name)
                raise Exception("Element could not be found! Please view the Screenshot!") from e
            except TimeoutException as t:
                self.driver.save_screenshot(self.direct + self.name)
                raise Exception("The test timed out! Please view the Screenshot!") from t
        return True

    def test_setting_cog(self):
        setting = self.driver.find_element_by_xpath("//android.view.View[contains(@bounds, '[1792,49][1859,105]')]")

        try:
            setting.click()
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                (By.XPATH, "//android.view.View[contains(@text, 'Support')]")))
            self.driver.press_keycode(4)
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                (By.XPATH, "//android.view.View[contains(@text, 'VIEW FULL TV GUIDE')]")))
        except NoSuchElementException as e:
            self.driver.save_screenshot(self.direct + self.name)
            raise Exception("Element could not be found! Please view the Screenshot!") from e
        except TimeoutException as t:
            self.driver.save_screenshot(self.direct + self.name)
            raise Exception("The test timed out! Please view the Screenshot!") from t
        return True

    def test_full_guide_button(self):
        full_guide = self.driver.find_element_by_xpath("//android.view.View[contains(@text, 'VIEW FULL TV GUIDE')]")

        try:
            full_guide.click()
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                (By.XPATH, "//android.view.View[contains(@text, 'TODAY')]")))
            self.driver.press_keycode(4)
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                (By.XPATH, "//android.view.View[contains(@text, 'VIEW FULL TV GUIDE')]")))
        except NoSuchElementException as e:
            self.driver.save_screenshot(self.direct + self.name)
            raise Exception("Element could not be found! Please view the Screenshot!") from e
        except TimeoutException as t:
            self.driver.save_screenshot(self.direct + self.name)
            raise Exception("The test timed out! Please view the Screenshot!") from t
        return True

    def test_guide_button(self):
        guide = self.driver.find_element_by_xpath("//android.view.View[contains(@resource-id, 'tv-guide')]")

        try:
            guide.click()
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                (By.XPATH, "//android.view.View[contains(@text, 'TODAY')]")))
            self.driver.press_keycode(4)
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                (By.XPATH, "//android.view.View[contains(@text, 'VIEW FULL TV GUIDE')]")))
        except NoSuchElementException as e:
            self.driver.save_screenshot(self.direct + self.name)
            raise Exception("Element could not be found! Please view the Screenshot!") from e
        except TimeoutException as t:
            self.driver.save_screenshot(self.direct + self.name)
            raise Exception("The test timed out! Please view the Screenshot!") from t
        return True


@pytest.mark.usefixtures("setup", "directory")
class TestGuideScreen:
    def test_scrolling_down(self):
        WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
            (By.XPATH, "//android.view.View[contains(@text, 'VIEW FULL TV GUIDE')]")))
        self.driver.find_element_by_xpath("//android.view.View[contains(@resource-id, 'tv-guide')]").click()
        WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
            (By.XPATH, "//android.view.View[contains(@text, 'TODAY')]")))

        for i in range(1, services):
            self.driver.press_keycode(20)
            self.driver.implicitly_wait(60)

        kcnc = self.driver.find_element_by_xpath("//android.view.View[contains(@bounds, '[0,949][318,1076]')]").text
        try:
            kcnc == 'KCNC'
        except NoSuchElementException as e:
            self.driver.save_screenshot(self.direct + self.name)
            raise Exception("Element could not be found! Please view the Screenshot!") from e
        except TimeoutException as t:
            self.driver.save_screenshot(self.direct + self.name)
            raise Exception("The test timed out! Please view the Screenshot!") from t
        return True

    def test_services_sidebar(self):
        self.driver.press_keycode(4)
        self.driver.find_element_by_xpath("//android.view.View[contains(@resource-id, 'tv-guide')]").click()
        WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
            (By.XPATH, "//android.view.View[contains(@text, 'TODAY')]")))

        for i in range(1, services):
            self.driver.press_keycode(23)
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                (By.XPATH, "//android.view.View[contains(@resource-id, 'BladeDetails')]")))
            self.driver.press_keycode(4)
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                (By.XPATH, "//android.view.View[contains(@text, 'TODAY')]")))
            self.driver.press_keycode(20)

        kcnc = self.driver.find_element_by_xpath("//android.view.View[contains(@bounds, '[0,949][318,1076]')]").text
        try:
            kcnc == 'KCNC'
        except NoSuchElementException as e:
            self.driver.save_screenshot(self.direct + self.name)
            raise Exception("Element could not be found! Please view the Screenshot!") from e
        except TimeoutException as t:
            self.driver.save_screenshot(self.direct + self.name)
            raise Exception("The test timed out! Please view the Screenshot!") from t
        return True

    """def test_services_livetv(self):
        self.driver.press_keycode(4)
        self.driver.find_element_by_xpath("//android.view.View[contains(@resource-id, 'tv-guide')]").click()
        WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
            (By.XPATH, "//android.view.View[contains(@text, 'TODAY')]")))

        for i in range(1, self.services):
            self.driver.press_keycode(23)
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                (By.XPATH, "//android.view.View[contains(@resource-id, 'BladeDetails')]")))
            self.driver.press_keycode(23)
            time.sleep(5)
            self.driver.press_keycode(4)
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                (By.XPATH, "//android.view.View[contains(@text, 'TODAY')]")))
            self.driver.press_keycode(20)

            kcnc = self.driver.find_element_by_xpath("//android.view.View[contains(@bounds, '[0,949][318,1076]')]").text
            try:
                kcnc == 'KCNC'
            except NoSuchElementException as e:
                self.driver.save_screenshot(self.direct + self.name)
                raise Exception("Element could not be found! Please view the Screenshot!") from e
            except TimeoutException as t:
                self.driver.save_screenshot(self.direct + self.name)
                raise Exception("The test timed out! Please view the Screenshot!") from t
            return True"""

    def test_setting_cog(self):
        self.driver.press_keycode(4)
        self.driver.find_element_by_xpath("//android.view.View[contains(@resource-id, 'tv-guide')]").click()
        WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
            (By.XPATH, "//android.view.View[contains(@text, 'TODAY')]")))
        setting = self.driver.find_element_by_xpath("//android.view.View[contains(@bounds, '[1792,49][1859,105]')]")

        try:
            setting.click()
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                (By.XPATH, "//android.view.View[contains(@text, 'Support')]")))
            self.driver.press_keycode(4)
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                (By.XPATH, "//android.view.View[contains(@text, 'TODAY')]")))
        except NoSuchElementException as e:
            self.driver.save_screenshot(self.direct + self.name)
            raise Exception("Element could not be found! Please view the Screenshot!") from e
        except TimeoutException as t:
            self.driver.save_screenshot(self.direct + self.name)
            raise Exception("The test timed out! Please view the Screenshot!") from t
        return True

    def test_home_button(self):
        WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
            (By.XPATH, "//android.view.View[contains(@text, 'TODAY')]")))
        self.driver.press_keycode(19)
        home = self.driver.find_element_by_xpath("//android.view.View[contains(@resource-id, 'home')]")

        try:
            home.click()
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                (By.XPATH, "//android.view.View[contains(@text, 'VIEW FULL TV GUIDE')]")))
            self.driver.press_keycode(4)
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                (By.XPATH, "//android.view.View[contains(@text, 'TODAY')]")))
        except NoSuchElementException as e:
            self.driver.save_screenshot(self.direct + self.name)
            raise Exception("Element could not be found! Please view the Screenshot!") from e
        except TimeoutException as t:
            self.driver.save_screenshot(self.direct + self.name)
            raise Exception("The test timed out! Please view the Screenshot!") from t
        return True

    def test_guide_scroll_right(self):
        WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
            (By.XPATH, "//android.view.View[contains(@text, 'TODAY')]")))
        tday = self.driver.find_element_by_xpath("//android.view.View[contains(@bounds, '[326,224][678,279]')]").text
        iterate_num = int(40)

        for i in range(1, iterate_num):
            self.driver.press_keycode(22)
            time.sleep(1)

        try:
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                (By.XPATH, "//android.view.View[contains(@text, 'TOMORROW')]")))
            self.driver.find_element_by_xpath("//android.view.View[contains(@text, 'TOMORROW')]").is_displayed()
            tmrrw = self.driver.find_element_by_xpath("//android.view.View[contains(@bounds, '[1734,224][1920,279]')]")\
                .text
            tday_obj = datetime.strptime(tday, "%I:%M %p")
            tday_obj += timedelta(hours=22)
            tmrrw_obj = datetime.strptime(tmrrw, "%I:%M %p")
            assert tday_obj.time() == tmrrw_obj.time()
        except NoSuchElementException as e:
            self.driver.save_screenshot(self.direct + self.name)
            raise Exception("Element could not be found! Please view the Screenshot!") from e
        except TimeoutException as t:
            self.driver.save_screenshot(self.direct + self.name)
            raise Exception("The test timed out! Please view the Screenshot!") from t
        return True


@pytest.mark.usefixtures("setup", "directory")
class TestSettingScreen:
    def test_setting_support(self):
        WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
            (By.XPATH, "//android.view.View[contains(@text, 'VIEW FULL TV GUIDE')]")))
        self.driver.find_element_by_xpath("//android.view.View[contains(@bounds, '[1792,49][1859,105]')]").click()
        WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
            (By.XPATH, "//android.view.View[contains(@text, 'Support')]")))
        self.driver.press_keycode(20)
        time.sleep(1)
        self.driver.press_keycode(22)
        iterate_num = int(40)

        for i in range(1, iterate_num):
            self.driver.press_keycode(20)
            time.sleep(1)
        record = self.driver.find_element_by_xpath("//android.view.View[contains(@bounds, '[525,839][1375,884]')]").text
        try:
            record == 'Can I Record Shows?'
        except NoSuchElementException as e:
            self.driver.save_screenshot(self.direct + self.name)
            raise Exception("Element could not be found! Please view the Screenshot!") from e
        except TimeoutException as t:
            self.driver.save_screenshot(self.direct + self.name)
            raise Exception("The test timed out! Please view the Screenshot!") from t
        return True

    def test_setting_legal(self):
        self.driver.press_keycode(4)
        WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
            (By.XPATH, "//android.view.View[contains(@text, 'VIEW FULL TV GUIDE')]")))
        self.driver.find_element_by_xpath("//android.view.View[contains(@bounds, '[1792,49][1859,105]')]").click()
        WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
            (By.XPATH, "//android.view.View[contains(@text, 'Legal')]")))
        self.driver.press_keycode(20)
        time.sleep(1)
        self.driver.press_keycode(20)
        time.sleep(1)

        terms = self.driver.find_element_by_xpath("//android.view.View[contains(@bounds, '[525,567][1375,612]')]").text
        try:
            terms == 'Terms and Conditions'
        except NoSuchElementException as e:
            self.driver.save_screenshot(self.direct + self.name)
            raise Exception("Element could not be found! Please view the Screenshot!") from e
        except TimeoutException as t:
            self.driver.save_screenshot(self.direct + self.name)
            raise Exception("The test timed out! Please view the Screenshot!") from t
        return True


def teardown_module(module):
    subprocess.call(['python3', 'EventDataParser.py'])
    subprocess.call(['python3', 'OnStreamMoveFiles.py'])
    return module
