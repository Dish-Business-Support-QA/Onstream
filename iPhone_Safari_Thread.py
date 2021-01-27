import os
import pandas as pd
import subprocess
from threading import Thread
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from appium.webdriver.appium_service import AppiumService
from appium import webdriver

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
version = '1.2.32'
device = 'iPhone 8-14.3'


class ChannelCount(object):
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
    desired_caps['nativeWebTap'] = True
    desired_caps['safariAllowPopups'] = True
    desired_caps['safariOpenLinksInBackground'] = True
    driver = webdriver.Remote('http://localhost:4723/wd/hub', desired_caps)
    dishtv = "https://test.watchdishtv.com/"
    driver.get(dishtv)
    WebDriverWait(driver, 30).until(ec.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/span/button/div'))).click()  # Click on the Hamburger
    WebDriverWait(driver, 30).until(ec.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/div[2]/span/span[2]/a/span'))).click()  # Click on the TV Guide button
    WebDriverWait(driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[2]/div/div/div/div[1]/div[1]')))  # Wait for Today to populate
    links = []
    channels = driver.find_elements(By.XPATH, '(//a[@class="_2eB_OXy4vbP1Kd9moNzO4j"])')  # Collect all of the channels
    for i in range(len(channels)):
        links.append(channels[i].get_attribute("href"))
    all_channels = list(dict.fromkeys(links))
    first_channel = all_channels[0].split('/')[5]
    driver.quit()


class GetService(object):
    url = r'http://uplink.jameslong.name/chan1000.html'
    tables = pd.read_html(url)
    s = tables[1]
    s = s.drop(s.index[0])
    service = s.iloc[:, 0:2]
    service.to_csv(r'/Users/dishbusiness/Desktop/OnStreamTestFiles/Logs/dish_channel_list.csv', header=["Service_Number", "Call_Letters"], index=False)
    service_number = float(ChannelCount.first_channel)
    df = pd.read_csv(r'/Users/dishbusiness/Desktop/OnStreamTestFiles/Logs/dish_channel_list.csv')
    try:
        call_letters = df.loc[df["Service_Number"] == service_number, 'Call_Letters'].values[0]
        call_letters = str(call_letters)
    except IndexError:
        for i in range(len(ChannelCount.channels)):
            next_channel = ChannelCount.all_channels[i].split('/')[5]
            service_number = float(next_channel)
            try:
                if df.loc[df["Service_Number"] == service_number, 'Call_Letters'].values[0]:
                    call_letters = df.loc[df["Service_Number"] == service_number, 'Call_Letters'].values[0]
                    call_letters = str(call_letters)
                    break
                else:
                    pass
            except IndexError:
                pass


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
        self.change = 40

    def get_number(self):
        return self.change


mc = CountRun()
cc = ChannelChange()


def pytest_run():
    channels = ChannelCount.all_channels
    while int(len(channels)) < int(cc.get_number()):
        mc.increment()
        mc.save_value()
        subprocess.run(['pytest', '--pytest-influxdb', '--influxdb_project=iPhone_Safari', '--influxdb_run_id=' + str(mc.get_value()), os.path.join(test_path, 'OnStream_iPhone_Safari.py'), '-sv'])
        channels = ChannelCount.all_channels + channels


if __name__ == "__main__":
    t1 = Thread(target=pytest_run)
    t1.start()
    t1.join()
