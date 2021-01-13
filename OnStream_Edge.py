import os
import pytest
import time
import subprocess
import shutil
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException, JavascriptException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.common.keys import Keys
from datetime import datetime, timedelta
from influxdb import InfluxDBClient
from Edge_Thread import version, mc, ChannelCount
from msedge.selenium_tools import EdgeOptions
from selenium.webdriver.edge.service import Service

testrun = '1.0.9'

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
                "Browser": "Edge",
            },
            "time": time.time_ns(),
            "fields": {
                "events_title": "test start",
                "text": "This is the start of test " + mc.get_value() + " on firmware " + version + " tested on " + ChannelCount.dishtv,
                "tags": "Onstream" + "," + "Edge" + "," + mc.get_value() + "," + version + "," + ChannelCount.dishtv
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
                    "Browser": "Edge",
                },
                "time": time.time_ns(),
                "fields": {
                    "events_title": "test end",
                    "text": "This is the end of test " + mc.get_value() + " on firmware " + version + " tested on " + ChannelCount.dishtv,
                    "tags": "Onstream" + "," + "Edge" + "," + mc.get_value() + "," + version + "," + ChannelCount.dishtv
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
    """.split(':')[-1].split(' ')[0]"""
    direct = os.path.join(picture_path) + "/"
    request.cls.direct = direct
    request.cls.name = name
    yield


@pytest.fixture(scope="class")
def setup(request):
    caps = EdgeOptions()
    caps.use_chromium = True
    caps.headless = False
    service = Service(EdgeChromiumDriverManager().install())
    driver = webdriver.Edge(options=caps, service=service)
    dishtv = ChannelCount.dishtv
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


@pytest.mark.usefixtures("setup", "directory")
class TestVersion:
    def test_version(self):
        try:
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                (By.XPATH, '//button[@class="_2YXx31Mkp4UfixOG740yi7 schema_accent_background"]'))).click()
            self.driver.find_element(By.XPATH, '//a[@role="button"]').click()
            self.driver.find_element(By.XPATH, '//a[@class="_1jBpd9Hw7kDuuvGVNTNlax schema_accent_background_hover"]').click()
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                (By.XPATH, '//div[@class="_1sd7usVW7fcyKBYM7qUANM"]')))
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
                        "Browser": "Edge",
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
            loading_circle = self.driver.find_elements(By.XPATH, 
                '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, 
                '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                        "Browser": "Edge",
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
            loading_circle = self.driver.find_elements(By.XPATH, 
                '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, 
                '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
            self.driver.find_element(By.XPATH, '//a[contains(@href,"home")]').is_displayed()  # home
            self.driver.find_element(By.XPATH, '//a[contains(@href,"epg")]').is_displayed()  # guide
            self.driver.find_element(By.XPATH, '//a[@class="_2r6Lq2AYJyfbZABtJvL0D_"]').is_displayed()  # setting
            self.driver.find_element(By.XPATH, '//button[@class="_2YXx31Mkp4UfixOG740yi7 schema_accent_background"]').is_displayed()  # full guide
            self.driver.find_elements(By.XPATH, '//div[@class="_1iKpTFW64nBCEODaArwlyd _1encUiSOWTmH2vOVl5BZqy"]')
            self.driver.find_element(By.XPATH, '//button[@class="_2YXx31Mkp4UfixOG740yi7 null"]').is_displayed()
            # learn_more
            drop_down = self.driver.find_elements(By.XPATH, '//a[@class="_1jBpd9Hw7kDuuvGVNTNlax schema_accent_background_hover"]')
            live = self.driver.find_elements(By.XPATH, '//div[@class="_1iKpTFW64nBCEODaArwlyd _1encUiSOWTmH2vOVl5BZqy"]')
            for button in live:
                button.is_displayed()  # popular_channels
            for button1 in drop_down:
                button1.is_displayed()  # drop_down
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
                        "Browser": "Edge",
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
            loading_circle = self.driver.find_elements(By.XPATH, 
                '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, 
                '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
            self.driver.find_element(By.XPATH, '//button[@class="_2YXx31Mkp4UfixOG740yi7 null"]').is_enabled()
            # learn_more
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
                        "Browser": "Edge",
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
            loading_circle = self.driver.find_elements(By.XPATH, 
                '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, 
                '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                        "Browser": "Edge",
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
            loading_circle = self.driver.find_elements(By.XPATH, 
                '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, 
                '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                (By.XPATH, '//button[@class="_2YXx31Mkp4UfixOG740yi7 null"]'))).click()  # learn more
            while True:
                if len(self.driver.window_handles) == 1:  # see if a tab is open
                    print("no tab")
                else:
                    try:
                        self.driver.switch_to.window(self.driver.window_handles[1])  # switch to second tab
                        self.driver.find_element(By.XPATH, '//img[@alt="DISH Fiber logo"]')  # Dish fiber
                        self.driver.switch_to.window(self.driver.window_handles[0])  # switch back to tab one
                    except TimeoutException:
                        self.driver.find_element_by_tag_name('body').send_keys(Keys.COMMAND + 'w')
                        # switch to second tab
                        self.driver.switch_to.window(self.driver.window_handles[0])
                        WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                            (By.XPATH, '//img[@alt="DISH Fiber logo"]'))).is_displayed()  # dish fiber
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
                        "Browser": "Edge",
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
            loading_circle = self.driver.find_elements(By.XPATH, 
                '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, 
                '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "timeout error"


@pytest.mark.usefixtures("setup", "directory", "now_time")
class TestGuideScreen:
    def test_images_displayed(self):
        try:
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                (By.XPATH, '//button[@class="_2YXx31Mkp4UfixOG740yi7 schema_accent_background"]'))).click()
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                (By.XPATH, '//div[@class="_3s9BHby87YFunQATlfDFIG _13zgmvI0VzaLaUVl9-7siJ"]')))
            self.driver.find_element(By.XPATH, '//div[@class="_1oUh3apnwdwzBiB_Uw6seb "]').is_displayed()  # banner
            self.driver.find_element(By.XPATH, '//img[@alt="Dish Logo"]').is_displayed()  # dish
            self.driver.find_element(By.XPATH, '//img[@alt="Dish Logo"]').is_displayed()  # custom_logo
            self.driver.find_element(By.XPATH, '//div[@class="Wjmljsl8wM6YcCXO7StJi"]').is_displayed()  # line
            self.driver.find_element(By.XPATH, '//span[@class="_3BUdesL_Hri_ikvd5WhZhY _3A8PSs77Wrg10ciWiA2H_B  "]').is_displayed()  # underline
            self.driver.find_element(By.XPATH, '//div[@class="_2JbshVQf7cKfzSj6SAqTiq"]').is_displayed()  # channel logos
            self.driver.find_element(By.XPATH, '//div[@class="_3mtdocLQZjeofa83PD2_vL"]').is_displayed()  # vertical bar
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
                        "Browser": "Edge",
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
            loading_circle = self.driver.find_elements(By.XPATH, 
                '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, 
                '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                        "Browser": "Edge",
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
            loading_circle = self.driver.find_elements(By.XPATH, 
                '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, 
                '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
            self.driver.find_element(By.XPATH, '//div[@class="_33q8pPVDOZ2wsVJzvR3jdy"]').is_displayed()  # right arrow
            self.driver.find_element(By.XPATH, '//a[@class="_2GEDK4s6kna2Yfl6_0Q6c_"]').is_displayed()  # play button
            self.driver.find_element(By.XPATH, '//div[@class="_12Yya3OL4XVr3adIektRU6"]').is_displayed()
            # more info button
            self.driver.find_element(By.XPATH, '//a[contains(@href,"home")]').is_displayed()  # home button
            self.driver.find_element(By.XPATH, '//a[@class="_2r6Lq2AYJyfbZABtJvL0D_"]').is_displayed()  # Setting Cog
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
                        "Browser": "Edge",
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
            loading_circle = self.driver.find_elements(By.XPATH, 
                '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, 
                '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
            self.driver.find_element(By.XPATH, '//div[@class="_33q8pPVDOZ2wsVJzvR3jdy"]').is_enabled()  # right arrow
            self.driver.find_element(By.XPATH, '//a[@class="_2GEDK4s6kna2Yfl6_0Q6c_"]').is_enabled()  # play button
            self.driver.find_element(By.XPATH, '//div[@class="_12Yya3OL4XVr3adIektRU6"]').is_enabled()
            # more info button
            self.driver.find_element(By.XPATH, '//a[contains(@href,"home")]').is_enabled()  # home button
            self.driver.find_element(By.XPATH, '//a[@class="_2r6Lq2AYJyfbZABtJvL0D_"]').is_enabled()  # Setting Cog
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
                        "Browser": "Edge",
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
            loading_circle = self.driver.find_elements(By.XPATH, 
                '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, 
                '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "URL": ChannelCount.dishtv, 
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "timeout error"


@pytest.mark.usefixtures("setup", "directory", "now_time")
class TestSideBarScreen:
    def test_images_displayed(self):
        try:
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//button[@class="_2YXx31Mkp4UfixOG740yi7 schema_accent_background"]'))).click()
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="9491"]')))
            info = WebDriverWait(self.driver, 10).until(ec.presence_of_element_located((By.XPATH, '//img[@alt="9491"]')))  # go to the more info button
            info1 = ActionChains(self.driver).move_to_element_with_offset(info, 132.5, 25.5).perform()  # hover mouse over it
            ActionChains(self.driver).click(info1).perform()  # click the more info button
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="HIST"]')))
            self.driver.find_element(By.XPATH, '//div[@class="_2hHA9bFIq-vRi5vrWcTHJY"]').is_displayed()  # show picture
            self.driver.find_element(By.XPATH, '//div[@class="_1oUh3apnwdwzBiB_Uw6seb "]').is_displayed()  # banner
            self.driver.find_element(By.XPATH, '//img[@alt="Dish Logo"]').is_displayed()  # dish
            self.driver.find_element(By.XPATH, '//img[@alt="Dish Logo"]').is_displayed()  # custom_logo
            self.driver.find_element(By.XPATH, '//div[@class="Wjmljsl8wM6YcCXO7StJi"]').is_displayed()  # line
            self.driver.find_element(By.XPATH, '//span[@class="_3BUdesL_Hri_ikvd5WhZhY _3A8PSs77Wrg10ciWiA2H_B  "]').is_displayed()  # underline
            self.driver.find_element(By.XPATH, '//div[@class="_2JbshVQf7cKfzSj6SAqTiq"]').is_displayed()  # channel logos
            self.driver.find_element(By.XPATH, '//div[@class="_3mtdocLQZjeofa83PD2_vL"]').is_displayed()  # vertical bar
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
                        "Browser": "Edge",
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
            loading_circle = self.driver.find_elements(By.XPATH, 
                '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, 
                '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
            """self.driver.find_element(By.XPATH, '//div[@class="_1JoT790R-w1p_Jv3yX7LrI"]').is_displayed()  # channel name"""
            self.driver.find_element(By.XPATH, '//div[@class="QJgwfXrH2X5_BIUd7kMnu"]').is_displayed()
            # event name and time
            self.driver.find_element(By.XPATH, '//div[@class="_1AhFoq9LRVrQE0BrdpGozJ schema_epgTimelineColors_background"]').is_displayed()  # TODAY
            self.driver.find_element(By.XPATH, '//div[contains(text(), "%s")]' % self.now).is_displayed()  # Time 1
            self.driver.find_element(By.XPATH, '//div[contains(text(), "%s")]' % self.now1).is_displayed()  # Time 2
            self.driver.find_element(By.XPATH, '//div[contains(text(), "%s")]' % self.now2).is_displayed()  # Time 3
            self.driver.find_element(By.XPATH, '//div[contains(text(), "%s")]' % self.now3).is_displayed()  # Time 4
            self.driver.find_element(By.XPATH, '//span[contains(text(), "MORE INFO")]').is_displayed()  # More Info
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
                        "Browser": "Edge",
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
            loading_circle = self.driver.find_elements(By.XPATH, 
                '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, 
                '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
            self.driver.find_element(By.XPATH, '//button[@class="_1Xyb-h8ETwWmEllf3HIy58"]').is_displayed()
            # exit button
            self.driver.find_element(By.XPATH, '//span[contains(text(), "WATCH LIVE")]').is_displayed()  # Watch Live
            self.driver.find_element(By.XPATH, '//div[@class="_12Yya3OL4XVr3adIektRU6"]').is_displayed()
            # more info button
            self.driver.find_element(By.XPATH, '//a[contains(@href,"home")]').is_displayed()  # home button
            self.driver.find_element(By.XPATH, '//a[@class="_2r6Lq2AYJyfbZABtJvL0D_"]').is_displayed()  # Setting Cog
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
                        "Browser": "Edge",
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
            loading_circle = self.driver.find_elements(By.XPATH, 
                '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, 
                '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
            self.driver.find_element(By.XPATH, '//button[@class="_1Xyb-h8ETwWmEllf3HIy58"]').is_enabled()
            # exit button
            self.driver.find_element(By.XPATH, '//div[@class="_12Yya3OL4XVr3adIektRU6"]').is_enabled()
            # more info button
            self.driver.find_element(By.XPATH, '//a[contains(@href,"home")]').is_enabled()  # home button
            self.driver.find_element(By.XPATH, '//a[@class="_2r6Lq2AYJyfbZABtJvL0D_"]').is_enabled()  # Setting Cog
            self.driver.find_element(By.XPATH, '//span[contains(text(), "WATCH LIVE")]').is_enabled()  # Watch Live
            self.driver.find_element(By.XPATH, '//span[contains(text(), "WATCH LIVE")]').click()  # Watch Live
            WebDriverWait(self.driver, 30).until_not(ec.presence_of_element_located(
                (By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')))
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
                        "Browser": "Edge",
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
            loading_circle = self.driver.find_elements(By.XPATH, 
                '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, 
                '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "timeout error"


@pytest.mark.usefixtures("setup", "directory", "now_time")
class TestLiveTV:
    def test_images_displayed(self):
        try:
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//button[@class="_2YXx31Mkp4UfixOG740yi7 schema_accent_background"]'))).click()
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="9491"]')))
            if ":" + str(30) in self.now:
                try:
                    service = WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located(
                        (By.XPATH, '(//a[@href="#/player/9491"])[1]')))  # go to the play button
                    ActionChains(self.driver).move_to_element(service).perform()  # hover mouse over it
                    ActionChains(self.driver).click(service).perform()  # click on the service
                except JavascriptException:
                    service = WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located(
                        (By.XPATH, '(//a[@href="#/player/9491"])[2]')))  # go to the play button
                    ActionChains(self.driver).move_to_element(service).perform()  # hover mouse over it
                    ActionChains(self.driver).click(service).perform()  # click on the service
                    pass
            else:
                service = WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                    (By.XPATH, '(//a[@href="#/player/9491"])[2]')))  # go to the play button
                ActionChains(self.driver).move_to_element(service).perform()  # hover mouse over it
                ActionChains(self.driver).click(service).perform()  # click on the service
            WebDriverWait(self.driver, 30).until_not(ec.presence_of_element_located(
                (By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')))
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//img[@id="bmpui-id-32"]')))
            # wait for loading screen to disappear
            self.driver.find_element(By.XPATH, '//span[@class="bmpui-ui-label bmpui-miniEpgToggleLabel"]').click()
            # click on the mini guide
            self.driver.find_element(By.XPATH, '//div[@class="bmpui-container-wrapper"]').is_displayed()  # Channel logo top right
            self.driver.find_element(By.XPATH, '//img[@alt="17612"]').is_displayed()  # Channel logo in mini guide
            self.driver.find_element(By.XPATH, '//div[@class="bmpui-ui-container bmpui-divider"]').is_displayed()
            # divider
            self.driver.find_element(By.XPATH, '//div[@class="bmpui-ui-container bmpui-fullTvGuideIcon"]').is_displayed()
            # Left Arrow
            self.driver.find_element(By.XPATH, '//span[@class="bmpui-ui-label bmpui-miniEpgToggleLabel"]').is_displayed()
            # Down Arrow
            self.driver.find_element(By.XPATH, '//div[@class="_33q8pPVDOZ2wsVJzvR3jdy"]').is_displayed()
            # Right Arrow
            self.driver.find_element(By.XPATH, '//div[@class="bmpui-ui-container bmpui-moreInfoIcon"]').is_displayed()
            # info emblem
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
                        "Browser": "Edge",
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
            loading_circle = self.driver.find_elements(By.XPATH, 
                '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, 
                '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
            self.driver.find_element(By.XPATH, '//span[@class="bmpui-ui-label bmpui-title"]').is_displayed()
            # Show title
            self.driver.find_element(By.XPATH, '//span[@class="bmpui-ui-label bmpui-subTitle"]').is_displayed()
            # Show episode
            self.driver.find_element(By.XPATH, '//span[text()="FULL TV GUIDE"]').is_displayed()
            # Full TV Guide
            """self.driver.find_element(By.XPATH, '//span[@class="bmpui-ui-playbacktimelabel"]').is_displayed()
            # Run Time of Service
            self.driver.find_element(By.XPATH, '//span[@class="bmpui-ui-playbacktimelabel bmpui-text-right"]').is_displayed()"""
            # Time left of Service
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
                        "Browser": "Edge",
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
            loading_circle = self.driver.find_elements(By.XPATH, 
                '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, 
                '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
            self.driver.find_element(By.XPATH, '//div[@class="bmpui-ui-container bmpui-fullTvGuideIcon"]').is_displayed()
            # Full TV Guide back button
            self.driver.find_element(By.XPATH, '//div[@class="bmpui-ui-container bmpui-moreInfoIcon"]').is_displayed()
            # More Info button
            self.driver.find_element(By.XPATH, '//span[@class="bmpui-ui-label bmpui-miniEpgToggleLabel"]').is_displayed()
            # Mini Guide down button
            self.driver.find_element(By.XPATH, '//div[@class="_33q8pPVDOZ2wsVJzvR3jdy"]').is_displayed()
            # Mini Guide right arrow button
            self.driver.find_element(By.XPATH, '//div[@class="_12Yya3OL4XVr3adIektRU6"]').is_displayed()
            # Mini Guide More Info button
            self.driver.find_element(By.XPATH, '//a[@class="_2GEDK4s6kna2Yfl6_0Q6c_"]').is_displayed()  # play button
            self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-volumetogglebutton bmpui-unmuted"]').is_displayed()
            # Mute button
            self.driver.find_element(By.XPATH, '//div[@class="bmpui-seekbar-markers"]').is_displayed()  # Seeker Bar
            """self.driver.find_element_by_xpath \
                ('//div[@class="bmpui-seekbar-playbackposition-marker schema_accent_background"]').is_displayed()"""
            # Seeker Bar Dot
            self.driver.find_element(By.XPATH, '//button[@id="bmpui-id-18"]').is_displayed()
            # Cast button
            self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-cctogglebutton bmpui-off"]').is_displayed()
            # Closed Caption button
            self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-fullscreentogglebutton bmpui-off"]').is_displayed()
            # Full Screen button
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
                        "Browser": "Edge",
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
            loading_circle = self.driver.find_elements(By.XPATH, 
                '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, 
                '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
            self.driver.find_element(By.XPATH, '//div[@class="bmpui-ui-container bmpui-fullTvGuideIcon"]').is_enabled()
            # Full TV Guide back button
            self.driver.find_element(By.XPATH, '//div[@class="bmpui-ui-container bmpui-moreInfoIcon"]').is_enabled()
            # More Info button
            self.driver.find_element(By.XPATH, '//span[@class="bmpui-ui-label bmpui-miniEpgToggleLabel"]').is_enabled()
            # Mini Guide down button
            self.driver.find_element(By.XPATH, '//div[@class="_33q8pPVDOZ2wsVJzvR3jdy"]').is_enabled()
            # Mini Guide right arrow button
            self.driver.find_element(By.XPATH, '//div[@class="_12Yya3OL4XVr3adIektRU6"]').is_enabled()
            # Mini Guide More Info button
            self.driver.find_element(By.XPATH, '//a[@class="_2GEDK4s6kna2Yfl6_0Q6c_"]').is_enabled()  # play button
            self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-volumetogglebutton bmpui-unmuted"]').is_enabled()
            # Mute button
            self.driver.find_element(By.XPATH, '//div[@class="bmpui-seekbar-markers"]').is_enabled()  # Seeker Bar
            """self.driver.find_element_by_xpath \
                ('//div[@class="bmpui-seekbar-playbackposition-marker schema_accent_background"]').is_enabled()"""
            # Seeker Bar Dot
            self.driver.find_element(By.XPATH, '//button[@id="bmpui-id-18"]').is_enabled()
            # Cast button
            self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-cctogglebutton bmpui-off"]').is_enabled()
            # Closed Caption button
            self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-fullscreentogglebutton bmpui-off"]').is_enabled()
            # Full Screen button
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
                        "Browser": "Edge",
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
            loading_circle = self.driver.find_elements(By.XPATH, 
                '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, 
                '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "timeout error"

    def test_control_bar_functions(self):
        try:
            #  turn mute button off and on
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//button[@data-bmpui-volume-level-tens="10"]')))
            self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-volumetogglebutton bmpui-unmuted"]').click()  # Mute button turn on
            self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-volumetogglebutton bmpui-muted"]').is_displayed()  # Mute button on
            self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-volumetogglebutton bmpui-muted"]').click()  # Mute button turn off
            self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-volumetogglebutton bmpui-unmuted"]').is_displayed()  # Mute button off
            # volume slider bar
            slider = WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//div[@class="bmpui-ui-volumeslider"]')))
            ActionChains(self.driver).click_and_hold(slider).move_by_offset(10, 0).release().perform()
            if WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                    (By.XPATH, '(//div[@aria-valuenow="55"])'))):
                assert True
            else:
                assert False, "Volume did not increase on the slider volume bar"
            #  turn full screen off and on
            self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-fullscreentogglebutton bmpui-off"]').click()  # turn full screen on
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located(
                (By.XPATH, '//button[@class="bmpui-ui-fullscreentogglebutton bmpui-on"]')))  # full screen on
            self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-fullscreentogglebutton bmpui-on"]').click()  # turn full screen off
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located(
                (By.XPATH, '//button[@class="bmpui-ui-fullscreentogglebutton bmpui-off"]')))  # full screen off
            # turn CC button off and on
            if WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//button[@class="bmpui-ui-cctogglebutton bmpui-off"]'))):
                WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//button[@class="bmpui-ui-cctogglebutton bmpui-off"]'))).click()  # CC button turn on
                WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located(
                    (By.XPATH, '//button[@class="bmpui-ui-cctogglebutton bmpui-on"]')))  # CC button on
                WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                    (By.XPATH, '//button[@class="bmpui-ui-cctogglebutton bmpui-on"]'))).click()  # CC button turn off
                self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-cctogglebutton bmpui-off"]').is_displayed()  # CC button off
            else:
                assert False, "Program could be on a commercial, please check screenshot"
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//button[@class="bmpui-ui-cctogglebutton bmpui-off"]'))).click()  # CC button turn on
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//span[@class="bmpui-ui-label bmpui-miniEpgToggleLabel"]'))).click()  # Closed Mini Guide
            if WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//div[@class="bmpui-ui-subtitle-overlay bmpui-cea608"]'))):
                assert True
            elif self.driver.find_element(By.XPATH, '//div[@class="bmpui-ui-subtitle-overlay bmpui-hidden"]'):
                assert False, "Program could be on commercial, please check screenshot"
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
                        "Browser": "Edge",
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
            loading_circle = self.driver.find_elements(By.XPATH, 
                '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, 
                '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
class TestSupportSettingsScreen:
    def test_images_displayed(self):
        try:
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                (By.XPATH, '//button[@class="_2YXx31Mkp4UfixOG740yi7 schema_accent_background"]'))).click()
            self.driver.find_element(By.XPATH, '//a[@role="button"]').click()
            self.driver.find_element(By.XPATH, '//a[@class="_1jBpd9Hw7kDuuvGVNTNlax schema_accent_background_hover"]').click()
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                (By.XPATH, '//div[@class="_1sd7usVW7fcyKBYM7qUANM"]')))
            self.driver.find_element(By.XPATH, '//div[@class="_1sd7usVW7fcyKBYM7qUANM"]').is_displayed()
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
                        "Browser": "Edge",
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
            loading_circle = self.driver.find_elements(By.XPATH, 
                '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, 
                '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
            self.driver.find_element(By.XPATH, '//h2[contains(text(), "Frequently Asked Questions")]').is_displayed()  # Freq asked questions
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//p[contains(text(), "How can I watch OnStream?")]')))
            """self.driver.find_element_by_xpath \
                ('//p[contains(text(), "How can I watch OnStream?")]').is_displayed()"""
            """self.driver.find_element_by_xpath\
                ('//p[contains(text(), "What devices are supported by OnStream? - Claudio’s Test")]').is_displayed()"""  # suported devices
            self.driver.find_element(By.XPATH, '//p[contains(text(), "When I leave my property why do I lose access to OnStream?")]').is_displayed()  # additional channels
            self.driver.find_element(By.XPATH, '//p[contains(text(), "What internet speed do I need to be able to use OnStream?")]').is_displayed()  # who to contact
            self.driver.find_element(By.XPATH, '//p[contains(text(), "What Channels does OnStream have?")]').is_displayed()  # how to cast
            self.driver.find_element(By.XPATH, '//p[contains(text(), "Are all channels live?")]').is_displayed()  # when I leave
            """self.driver.find_element_by_xpath\
                ('//p[contains(text(), "Can’t find the answer to what you’re looking for?")]').is_displayed()"""
            # can't find answers
            """self.driver.find_element_by_xpath\
                ('//p[contains(text(), "Please Call Dish Support at: ")]').is_displayed()  # call dish support
            self.driver.find_element_by_xpath\
                ('//p[contains(text(), "1-800-333-DISH")]').is_displayed()"""  # number to call
            app_version = self.driver.find_element(By.XPATH, '//p[@class="_2G-12UYHfG0a2MlL0pEXtD"]').text
            print(app_version, file=open(os.path.join(base_path, 'Logs', 'app_version.txt'), "w"))
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
                        "Browser": "Edge",
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
            loading_circle = self.driver.find_elements(By.XPATH, 
                '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, 
                '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
class TestLegalSettingsScreen:
    def test_images_displayed(self):
        try:
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//button[@class="_2YXx31Mkp4UfixOG740yi7 schema_accent_background"]'))).click()
            self.driver.find_element(By.XPATH, '//a[@role="button"]').click()
            self.driver.find_element(By.XPATH, '//a[@class="_1jBpd9Hw7kDuuvGVNTNlax schema_accent_background_hover"][2]').click()
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//div[@class="_2hNvqt9m_HItaYpgkx528X"]')))
            self.driver.find_element(By.XPATH, '//div[@class="_2hNvqt9m_HItaYpgkx528X"]').is_displayed()
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
                        "Browser": "Edge",
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
            loading_circle = self.driver.find_elements(By.XPATH, 
                '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, 
                '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
            self.driver.find_element(By.XPATH, '//h2[contains(text(), "Legal")]').is_displayed()  # Legal
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//h4[contains(text(), "Service Agreement")]')))
            """self.driver.find_element_by_xpath\
                ('//h4[contains(text(), "Service Agreement")]').is_displayed()"""  # Service Agreements
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//h4[contains(text(), "Terms and Conditions")]')))
            """self.driver.find_element_by_xpath\
                ('//h4[contains(text(), "Terms and conditions")]').is_displayed()"""  # Terms and conditions
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
                        "Browser": "Edge",
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
            loading_circle = self.driver.find_elements(By.XPATH, 
                '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, 
                '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "timeout error"

    def test_link1_clickable(self):
        try:
            self.driver.find_element(By.XPATH, '//a[@href="https://www.dish.com/service-agreements/"]').click()
            self.driver.find_element(By.XPATH, '//h1[contains(text(), "DISH Network Service Agreements")]').is_displayed()
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
                        "Browser": "Edge",
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
            loading_circle = self.driver.find_elements(By.XPATH, 
                '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, 
                '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "timeout error"

    def test_link2_clickable(self):
        try:
            self.driver.get(self.dishtv)
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//button[@class="_2YXx31Mkp4UfixOG740yi7 schema_accent_background"]'))).click()
            self.driver.find_element(By.XPATH, '//a[@role="button"]').click()
            self.driver.find_element(By.XPATH, '//a[@class="_1jBpd9Hw7kDuuvGVNTNlax schema_accent_background_hover"][2]').click()
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//div[@class="_2hNvqt9m_HItaYpgkx528X"]')))
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//a[@href="https://www.dish.com/terms-conditions/"]'))).click()
            """self.driver.find_element(By.XPATH, '//a[@href="https://www.dish.com/terms-conditions/"]').click()"""
            self.driver.find_element(By.XPATH, '//h1[contains(text(), "Important Terms and Conditions")]').is_displayed()
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
                        "Browser": "Edge",
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
            loading_circle = self.driver.find_elements(By.XPATH, 
                '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH, 
                '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "timeout error"


@pytest.mark.usefixtures("setup", "directory", "now_time")
class TestServices:
    def test_services_configured(self):
        try:
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//button[@class="_2YXx31Mkp4UfixOG740yi7 schema_accent_background"]'))).click()
            WebDriverWait(self.driver, 30).until_not(ec.visibility_of_element_located((By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')))
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//img[@alt="9491"]')))
            links = []
            channels = self.driver.find_elements(By.XPATH, '(//a[@class="_2GEDK4s6kna2Yfl6_0Q6c_"])')
            for i in range(len(channels)):
                links.append(channels[i].get_attribute("href"))
            all_channels = list(dict.fromkeys(links))
            for link in all_channels:
                channel = link.strip().split('/')[5]
                self.driver.get(link)
                self.driver.refresh()
                try:
                    WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//button[@class="TGyzX_NHJqx9WzvYDiQ5g"]'))).is_enabled()
                    self.driver.find_element(By.XPATH, '//button[@class="TGyzX_NHJqx9WzvYDiQ5g"]').click()
                except TimeoutException:
                    pass
                WebDriverWait(self.driver, 30).until_not(ec.visibility_of_element_located(
                    (By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')))
                WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                    (By.XPATH, '//div[@class="bitmovinplayer-poster"]')))
                time.sleep(5)
                self.driver.save_screenshot(self.direct + str(channel) + ".png")
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
                        "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
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
                            "Browser": "Edge",
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "timeout error"