import subprocess
from appium import webdriver
from appium.webdriver.appium_service import AppiumService
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By

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

WebDriverWait(driver, 30).until(ec.presence_of_element_located(
    (By.XPATH, "//android.view.View[contains(@text, 'VIEW FULL TV GUIDE')]")))
driver.find_element_by_xpath("//android.view.View[contains(@resource-id, 'tv-guide')]").click()
WebDriverWait(driver, 30).until(ec.presence_of_element_located(
    (By.XPATH, "//android.view.View[contains(@text, 'TODAY')]")))
while True:
    try:
        driver.press_keycode(20)
        e2 = driver.find_element_by_xpath("//android.view.View[contains(@bounds, '[0,1075][318,1076]')][1]/*").text
    except NoSuchElementException as e:
        elements = driver.find_elements_by_xpath("//android.view.View[contains(@bounds, '[0,224][318,1076]')][1]/*")
        break

services = len(elements)
print(services)
driver.quit()