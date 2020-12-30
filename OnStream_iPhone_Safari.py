import os
import subprocess
import pytest
import json
import time
import shutil
from appium import webdriver
from datetime import datetime, timedelta
from appium.webdriver.appium_service import AppiumService
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from influxdb import InfluxDBClient
from iPhone_Safari_Thread import version, mc, ChannelCount, device, device_software, GetService

testrun = '1.2.1'

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


@pytest.fixture(scope="session", autouse=True)
def auto_start(request):
    test_start = [
        {
            "measurement": "OnStream",
            "tags": {
                "Software": version,
                "Test": mc.get_value(),
                "URL": ChannelCount.dishtv,
                "Browser": "Safari",
                "Device": device,
                "Device_Software": device_software,
            },
            "time": time.time_ns(),
            "fields": {
                "events_title": "test start",
                "text": "This is the start of test " + mc.get_value() + " on firmware " + version + " tested on " + ChannelCount.dishtv,
                "tags": "Onstream" + "," + "Safari" + "," + mc.get_value() + "," + version + "," + ChannelCount.dishtv
            }
        }
    ]
    client.write_points(test_start)

    def auto_fin():
        test_end = [
            {
                "measurement": "OnStream",
                "tags": {
                    "Software": version,
                    "Test": mc.get_value(),
                    "URL": ChannelCount.dishtv,
                    "Browser": "Safari",
                    "Device": device,
                    "Device_Software": device_software,
                },
                "time": time.time_ns(),
                "fields": {
                    "events_title": "test end",
                    "text": "This is the end of test " + mc.get_value() + " on firmware " + version + " tested on " + ChannelCount.dishtv,
                    "tags": "Onstream" + "," + "Safari" + "," + mc.get_value() + "," + version + "," + ChannelCount.dishtv
                }
            }
        ]
        client.write_points(test_end)
        try:
            Archived = os.path.join(base_path) + '/' + 'Archived' + '/' + testrun + '/' + mc.get_value()
            os.mkdir(Archived)
        except FileNotFoundError:
            tr = os.path.join(base_path) + '/' + 'Archived' + '/' + testrun
            os.mkdir(tr)
        except FileExistsError:
            Archived = os.path.join(base_path) + '/' + 'Archived' + '/' + testrun + '/' + mc.get_value() + 'duplicate'
            os.mkdir(Archived)

        Pictures = os.path.join(base_path) + '/' + 'Pictures' + '/'
        Duration = os.path.join(base_path) + '/' + 'Duration' + '/'

        dest = os.path.join(base_path, 'Archived') + '/' + testrun + '/' + mc.get_value()

        try:
            PicturesFile = os.listdir(Pictures)
            for f in PicturesFile:
                if not f.startswith('.'):
                    shutil.move(Pictures + f, dest)
        except FileNotFoundError:
            print("File Not Found at " + Pictures)
            pass

        try:
            DurationFile = os.listdir(Duration)
            for f in DurationFile:
                if not f.startswith('.'):
                    shutil.move(Duration + f, dest)
        except FileNotFoundError:
            print("File Not Found at " + Duration)
            pass
        subprocess.run(['python3', 'ClearFolders.py'])

    request.addfinalizer(auto_fin)


@pytest.fixture(scope="class")
def directory(request):
    name = os.environ.get('PYTEST_CURRENT_TEST')
    direct = '/Users/dishbusiness/Desktop/OnStreamTestFiles/Pictures/'
    request.cls.direct = direct
    request.cls.name = name
    yield


@pytest.fixture(scope="class")
def current_time(request):
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


@pytest.fixture(scope="class")
def setup(request):
    appium_service = AppiumService()
    appium_service.start()
    desired_caps = ChannelCount.desired_caps
    driver = webdriver.Remote('http://localhost:4723/wd/hub', desired_caps)
    driver.get('https://watchdishtv.com/')
    request.cls.driver = driver
    logo = "DaVita Logo"  # Big logo on home screen
    request.cls.logo = logo
    yield
    driver.quit()


@pytest.mark.usefixtures("setup", "directory")
class TestVersion:
    def test_version(self):
        try:
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//button[@class="_1ATKIs2nHrPvAu0b3sAXQz"]'))).click()
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//span[contains(text(), "Settings")]'))).click()
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//li[@class="_1c_-iIVNzHdk3aepkUNNWh schema_accent_border-bottom"]')))
            v = self.driver.find_element(By.XPATH, '//p[@class="_2G-12UYHfG0a2MlL0pEXtD"]')
            v = v.text.split(':')[1].strip()
            assert version == v
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": version,
                        "Test": mc.get_value(),
                        "Pytest": self.name,
                        "URL": ChannelCount.dishtv,
                        "Browser": "Safari",
                        "Device": device,
                        "Device_Software": device_software,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH, '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "timeout error"


@pytest.mark.usefixtures("setup", "directory")
class TestHomeScreen:
    def test_images_displayed(self):
        try:
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                (By.XPATH, '//button[@class="_2YXx31Mkp4UfixOG740yi7 schema_accent_background"]')))
            self.driver.find_element(By.XPATH, '//div[@class="_1oUh3apnwdwzBiB_Uw6seb "]').is_displayed()  # banner
            self.driver.find_element(By.XPATH, '//img[@alt="Dish Logo"]').is_displayed()  # dish
            self.driver.find_element(By.XPATH, '//img[@alt="Dish Logo"]').is_displayed()  # dish fiber
            self.driver.find_element(By.XPATH, '//img[@alt="' + self.logo + '"]').is_displayed()  # custom_logo
            self.driver.find_element(By.XPATH, '//div[@class="Wjmljsl8wM6YcCXO7StJi"]').is_displayed()  # line
            self.driver.find_element(By.XPATH, '//div[@class="_3h0DRYR6lHf63mKPlX9zwF"]').is_displayed()  # background
            self.driver.find_element(By.XPATH, '//span[@class="_3BUdesL_Hri_ikvd5WhZhY _3A8PSs77Wrg10ciWiA2H_B  "]').is_displayed()  # underline
            self.driver.find_element(By.XPATH, '//div[@class="_2DNEUdY-mRumdYpM8xTEN5"]').is_displayed()  # bottom_image
            self.driver.find_element(By.XPATH, '//a[@class="_2r6Lq2AYJyfbZABtJvL0D_"]').is_displayed()  # setting
            self.driver.find_element(By.XPATH, '//hr[@class="K22SRFwz7Os1KInw2zPCQ"]').is_displayed()  # thin_line
            live = self.driver.find_elements(By.XPATH, '//div[@class="_1acuZqkpaJBNYrvoPzBNq_ _1Ec0IteN1F_Ae9opzh37wr"]')
            for image in live:
                image.is_displayed()  # popular_channels
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": version,
                        "Test": mc.get_value(),
                        "Pytest": self.name,
                        "URL": ChannelCount.dishtv,
                        "Browser": "Safari",
                        "Device": device,
                        "Device_Software": device_software,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH, '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "timeout error"

    def test_buttons_enabled(self):
        try:
            self.driver.find_element(By.XPATH, '//a[contains(@href,"home")]').is_enabled()  # home
            self.driver.find_element(By.XPATH, '//a[contains(@href,"epg")]').is_enabled()  # guide
            self.driver.find_element(By.XPATH, '//a[@class="_2r6Lq2AYJyfbZABtJvL0D_"]').is_enabled()  # setting
            self.driver.find_element(By.XPATH, '//button[@class="_2YXx31Mkp4UfixOG740yi7 schema_accent_background"]').is_enabled()  # full_guide
            self.driver.find_element(By.XPATH, '//button[@class="_2YXx31Mkp4UfixOG740yi7 null"]').is_enabled()  # learn_more
            drop_down = self.driver.find_elements(By.XPATH, '//a[@class="_1jBpd9Hw7kDuuvGVNTNlax schema_accent_background_hover"]')
            live = self.driver.find_elements(By.XPATH, '//a[@class="_2JuEPUlHoO3FulobzI50N5 _3RunNS41fFzaeBFbJ1JGwa schema_popularChannelsColors_background"]')
            for button in drop_down:
                button.is_enabled()  # drop_down
            for button1 in live:
                button1.is_enabled()  # live
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": version,
                        "Test": mc.get_value(),
                        "Pytest": self.name,
                        "URL": ChannelCount.dishtv,
                        "Browser": "Safari",
                        "Device": device,
                        "Device_Software": device_software,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH, '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "timeout error"

    def test_text_displayed(self):
        try:
            self.driver.find_element(By.XPATH, '//span[contains(text(), "Home")]')  # home
            self.driver.find_element(By.XPATH, '//span[contains(text(), "TV Guide")]')  # guide
            self.driver.find_element(By.XPATH, '//button[contains(text(), "VIEW FULL TV GUIDE")]')  # full_guide
            self.driver.find_element(By.XPATH, '//div[contains(text(), "Most Popular Channels")]')  # pop_channels
            self.driver.find_element(By.XPATH, '//div[contains(text(), "Want more channels, a DVR, or additional features?")]')  # question
            self.driver.find_element(By.XPATH, '//div[contains(text(), "Call 866-794-6166")]')  # number
            live = self.driver.find_elements(By.XPATH, '//div[@class="_1MhUC88bcyh64jOZVIlotn _3DE_w36fN1va108RdAiaue" and text()="WATCH TV"]')
            for text in live:
                text.is_displayed()  # watch_live
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": version,
                        "Test": mc.get_value(),
                        "Pytest": self.name,
                        "URL": ChannelCount.dishtv,
                        "Browser": "Safari",
                        "Device": device,
                        "Device_Software": device_software,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH, '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "timeout error"

    def test_link_clickable(self):
        try:
            self.driver.execute_script("mobile: scroll", {'direction': 'down'})
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//button[@class="_2YXx31Mkp4UfixOG740yi7 null"]')))  # learn more
            self.driver.find_element(By.XPATH, '//button[contains(text(), "Learn More")]').click()
            while True:
                if len(self.driver.window_handles) == 1:  # see if a tab is open
                    print("no tab")
                else:
                    try:
                        time.sleep(5)
                        self.driver.switch_to.window(self.driver.window_handles[1])  # switch to second tab
                        self.driver.find_element(By.XPATH, '//img[@alt="DISH Fiber logo"]')  # Dish fiber
                        self.driver.switch_to.window(self.driver.window_handles[0])  # switch back to tab one
                    except TimeoutException:
                        self.driver.find_element_by_tag_name('body').send_keys(Keys.COMMAND + 'w')  # switch to second tab
                        self.driver.switch_to.window(self.driver.window_handles[0])
                        WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//img[@alt="DISH Fiber logo"]'))).is_displayed()  # dish fiber
                        self.driver.switch_to.window(self.driver.window_handles[0])  # switch back to tab one
                    break
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": version,
                        "Test": mc.get_value(),
                        "Pytest": self.name,
                        "URL": ChannelCount.dishtv,
                        "Browser": "Safari",
                        "Device": device,
                        "Device_Software": device_software,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH, '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "timeout error"


@pytest.mark.usefixtures("setup", "directory", "current_time")
class TestGuideScreen:
    def test_images_displayed(self):
        try:
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//button[@class="_1ATKIs2nHrPvAu0b3sAXQz"]'))).click()
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//span[contains(text(), "TV Guide")]'))).click()
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="%s"]' % ChannelCount.first_channel)))
            self.driver.find_element(By.XPATH, '//div[@class="_1oUh3apnwdwzBiB_Uw6seb "]').is_displayed()  # banner
            self.driver.find_element(By.XPATH, '//img[@alt="Dish Logo"]').is_displayed()  # dish
            self.driver.find_element(By.XPATH, '//img[@alt="Dish Logo"]').is_displayed()  # custom_logo
            self.driver.find_element(By.XPATH, '//div[@class="Wjmljsl8wM6YcCXO7StJi"]').is_displayed()  # line
            self.driver.find_element(By.XPATH, '//span[@class="_3BUdesL_Hri_ikvd5WhZhY _3A8PSs77Wrg10ciWiA2H_B  "]').is_displayed()  # underline
            self.driver.find_element(By.XPATH, '//div[@class="_2JbshVQf7cKfzSj6SAqTiq"]').is_displayed()  # channel logos
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": version,
                        "Test": mc.get_value(),
                        "Pytest": self.name,
                        "URL": ChannelCount.dishtv,
                        "Browser": "Safari",
                        "Device": device,
                        "Device_Software": device_software,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH, '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "timeout error"

    def test_text_displayed(self):
        try:
            self.driver.find_element(By.XPATH, '//div[@class="_1AhFoq9LRVrQE0BrdpGozJ schema_epgTimelineColors_background"]').is_displayed()  # TODAY
            self.driver.find_element(By.XPATH, '//div[contains(text(), "%s")]' % self.now).is_displayed()  # Time 1
            self.driver.find_element(By.XPATH, '//div[contains(text(), "%s")]' % self.now1).is_displayed()  # Time 2
            self.driver.find_element(By.XPATH, '//div[contains(text(), "%s")]' % self.now2).is_displayed()  # Time 3
            self.driver.find_element(By.XPATH, '//div[contains(text(), "%s")]' % self.now3).is_displayed()  # Time 4
            self.driver.find_element(By.XPATH, '//span[contains(text(), "MORE INFO")]').is_displayed()  # More Info
            self.driver.find_element(By.XPATH, '//span[contains(text(), "WATCH LIVE")]').is_displayed()  # Watch Live
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": version,
                        "Test": mc.get_value(),
                        "Pytest": self.name,
                        "URL": ChannelCount.dishtv,
                        "Browser": "Safari",
                        "Device": device,
                        "Device_Software": device_software,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH, '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "timeout error"

    def test_buttons_displayed(self):
        try:
            self.driver.find_element(By.XPATH, '//button[@class="_1ATKIs2nHrPvAu0b3sAXQz"]').is_displayed()  # Setting Cog
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": version,
                        "Test": mc.get_value(),
                        "Pytest": self.name,
                        "URL": ChannelCount.dishtv,
                        "Browser": "Safari",
                        "Device": device,
                        "Device_Software": device_software,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH, '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "timeout error"

    def test_buttons_clickable(self):
        try:
            self.driver.find_element(By.XPATH, '//button[@class="_1ATKIs2nHrPvAu0b3sAXQz"]').is_displayed()  # Setting Cog
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": version,
                        "Test": mc.get_value(),
                        "Pytest": self.name,
                        "URL": ChannelCount.dishtv,
                        "Browser": "Safari",
                        "Device": device,
                        "Device_Software": device_software,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH, '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "timeout error"


@pytest.mark.usefixtures("setup", "directory", "current_time")
class TestSideBarScreen:
    def test_images_displayed(self):
        try:
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//button[@class="_1ATKIs2nHrPvAu0b3sAXQz"]'))).click()
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//span[contains(text(), "TV Guide")]'))).click()
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="%s"]' % ChannelCount.first_channel)))
            channel = self.driver.find_elements(By.XPATH, '//div[@class="A7qtluKp_shMOW5H57lxU"]')
            channel[1].click()
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="%s"]' % GetService.call_letters)))
            self.driver.find_element(By.XPATH, '//div[@class="_2hHA9bFIq-vRi5vrWcTHJY"]').is_displayed()  # show picture
            self.driver.find_element(By.XPATH, '//div[@class="_2MN6t7M-yb_HV8dBhfN6gV"]').is_displayed()  # banner
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": version,
                        "Test": mc.get_value(),
                        "Pytest": self.name,
                        "URL": ChannelCount.dishtv,
                        "Browser": "Safari",
                        "Device": device,
                        "Device_Software": device_software,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH, '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "timeout error"

    def test_text_displayed(self):
        try:
            self.driver.find_element(By.XPATH, '//div[@class="_3fW8-VcO8a7nDEgrjCMnNy"]').is_displayed()  # program name
            self.driver.find_element(By.XPATH, '//div[@class="_2DEsD0Z30LigYsfLSOTKoV"]').is_displayed()  # date aired
            self.driver.find_element(By.XPATH, '//div[@class="_2r57e9dvMOVJLBMUNfC6SK"]').is_displayed()  # run-time
            self.driver.find_element(By.XPATH, '//div[@class="jssgKTzFuKGgoWOQeez7N"]').is_displayed()  # program description
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": version,
                        "Test": mc.get_value(),
                        "Pytest": self.name,
                        "URL": ChannelCount.dishtv,
                        "Browser": "Safari",
                        "Device": device,
                        "Device_Software": device_software,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH, '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "timeout error"

    def test_buttons_displayed(self):
        try:
            self.driver.find_element(By.XPATH, '//button[@class="_1Xyb-h8ETwWmEllf3HIy58"]').is_displayed()  # exit button
            self.driver.find_element(By.XPATH, '//span[contains(text(), "WATCH LIVE")]').is_displayed()  # Watch Live
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": version,
                        "Test": mc.get_value(),
                        "Pytest": self.name,
                        "URL": ChannelCount.dishtv,
                        "Browser": "Safari",
                        "Device": device,
                        "Device_Software": device_software,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH, '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "timeout error"

    def test_buttons_clickable(self):
        try:
            self.driver.find_element(By.XPATH, '//button[@class="_1Xyb-h8ETwWmEllf3HIy58"]').is_enabled()  # exit button
            self.driver.find_element(By.XPATH, '//span[contains(text(), "WATCH LIVE")]').is_enabled()  # Watch Live
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": version,
                        "Test": mc.get_value(),
                        "Pytest": self.name,
                        "URL": ChannelCount.dishtv,
                        "Browser": "Safari",
                        "Device": device,
                        "Device_Software": device_software,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH, '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "timeout error"


@pytest.mark.usefixtures("setup", "directory", "current_time")
class TestLiveTV:
    def test_images_displayed(self):
        try:
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//button[@class="_1ATKIs2nHrPvAu0b3sAXQz"]'))).click()  # click the hamburger
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//span[contains(text(), "TV Guide")]'))).click()  # click TV Guide
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="%s"]' % ChannelCount.first_channel)))  # wait for the guide to populate
            channel = self.driver.find_elements(By.XPATH, '//div[@class="_23r_4FmKovJreL51RFbebf schema_accent_fontColor"]')  # click a channel for ESPN
            channel[1].click()
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="%s"]' % GetService.call_letters)))  # wait for ESPN to appear
            self.driver.find_element(By.XPATH, '//span[contains(text(), "WATCH LIVE")]').click()  # Click Watch Live
            WebDriverWait(self.driver, 30).until_not(ec.presence_of_element_located((By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')))
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//img[@id="bmpui-id-32"]')))  # wait for loading screen to disappear
            self.driver.find_element(By.XPATH, '//li[contains(text(), "Mini Guide")]').click()  # click on the mini guide
            WebDriverWait(self.driver, 30).until_not(ec.visibility_of_element_located((By.XPATH, '//div[contains(text(), "Loading TV Guide...")]')))  # wait for mini guide to load
            self.driver.find_element(By.XPATH, '//img[@alt="%s"]' % GetService.call_letters).is_displayed()  # Channel logo top
            self.driver.find_element(By.XPATH, '//img[@alt="%s"]' % ChannelCount.first_channel).is_displayed()  # Channel logo in mini guide
            self.driver.find_element(By.XPATH, '//div[@class="bmpui-ui-container bmpui-divider"]').is_displayed()  # divider
            self.driver.find_element(By.XPATH, '//div[@class="bmpui-ui-container bmpui-fullTvGuideIcon"]').is_displayed()  # Left Arrow
            self.driver.find_element(By.XPATH, '//span[@class="bmpui-ui-label bmpui-miniEpgToggleLabel"]').is_displayed()  # Down Arrow
            self.driver.find_element(By.XPATH, '//div[@class="_33q8pPVDOZ2wsVJzvR3jdy"]').is_displayed()  # Right Arrow
            self.driver.find_element(By.XPATH, '//div[@class="bmpui-ui-container bmpui-moreInfoIcon"]').is_displayed()  # info emblem
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": version,
                        "Test": mc.get_value(),
                        "Pytest": self.name,
                        "URL": ChannelCount.dishtv,
                        "Browser": "Safari",
                        "Device": device,
                        "Device_Software": device_software,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH, '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": self.name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Safari",
                            "Device": device,
                            "Device_Software": device_software,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "timeout error"

