import os
import pytest
import time
import subprocess
import shutil
import platform
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException, ElementNotInteractableException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.opera import OperaDriverManager
from selenium.webdriver.common.keys import Keys
from datetime import datetime, timedelta
from influxdb import InfluxDBClient
from conftest import all_ld, active_service

browser = os.path.basename(__file__).split("_")[1]
plat = platform.platform().split('-')
device = str(plat[0] + "-" + plat[1])


@pytest.fixture(scope="session", autouse=True)
def client_setup(grafana_ip, grafana_port):
    client = InfluxDBClient(host=grafana_ip, port=grafana_port, database='ONSTREAM')
    return client


@pytest.fixture(scope="session", autouse=True)
def auto_start(request, onstream_version, onstream_url, client_setup):
    try:
        archive_version = os.path.abspath(os.curdir) + os.sep + 'Archived' + os.sep + onstream_version
        os.mkdir(archive_version)
    except FileNotFoundError:
        trd = os.path.abspath(os.curdir) + os.sep + 'Archived'
        os.mkdir(trd)
    except FileExistsError:
        pass

    count = 0
    for i in os.listdir(os.path.abspath(os.curdir) + os.sep + 'Archived' + os.sep + onstream_version):
        if not i.startswith('.'):
            count += 1

    testrun = count + 1
    try:
        archive = os.path.abspath(os.curdir) + os.sep + 'Archived' + os.sep + onstream_version + os.sep + str(browser) + '_' + str(testrun)
        os.mkdir(archive)
    except FileNotFoundError:
        at = os.path.abspath(os.curdir) + os.sep + 'Archived' + os.sep + onstream_version
        os.mkdir(at)
    except FileExistsError:
        pass
    test_start = [
        {
            "measurement": "OnStream",
            "tags": {
                "Software": onstream_version,
                "Test": 1,
                "URL": onstream_url,
                "Browser": "Opera",
                "Device": device,
            },
            "time": time.time_ns(),
            "fields": {
                "events_title": "test start",
                "text": "This is the start of test " + "1" + " on firmware " + onstream_version + " tested on " + onstream_url,
                "tags": "Onstream" + "," + "Opera" + "," + "1" + "," + onstream_version + "," + onstream_url
            }
        }
    ]
    client_setup.write_points(test_start)

    def auto_fin():
        test_end = [
            {
                "measurement": "OnStream",
                "tags": {
                    "Software": onstream_version,
                    "Test": 1,
                    "URL": onstream_url,
                    "Browser": "Opera",
                    "Device": device,
                },
                "time": time.time_ns(),
                "fields": {
                    "events_title": "test end",
                    "text": "This is the end of test " + "1" + " on firmware " + onstream_version + " tested on " + onstream_url,
                    "tags": "Onstream" + "," + "Opera" + "," + "1" + "," + onstream_version + "," + onstream_url
                }
            }
        ]
        client_setup.write_points(test_end)

        Pictures = os.path.abspath(os.curdir) + os.sep + 'Pictures' + os.sep
        Duration = os.path.abspath(os.curdir) + os.sep + 'Pictures' + os.sep

        dest = os.path.abspath(os.curdir) + os.sep + 'Archived' + os.sep + onstream_version + os.sep + str(browser) + '_' + str(testrun)

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
    direct = os.path.abspath(os.curdir) + os.sep + 'Pictures' + os.sep
    request.cls.direct = direct
    request.cls.name = name
    yield


@pytest.fixture(scope="class")
def setup(request, onstream_url, custom_logo):
    driver = webdriver.Opera(executable_path=OperaDriverManager().install())
    dishtv = onstream_url
    driver.get(dishtv)
    logo = custom_logo  # Big logo on home screen
    src = driver.page_source
    request.cls.driver = driver
    request.cls.src = src
    request.cls.dishtv = dishtv
    request.cls.logo = logo
    yield
    driver.quit()


@pytest.fixture(scope="class")
def current_time(request):
    t1 = datetime.now() + timedelta(hours=1)
    t2 = datetime.now() + timedelta(hours=2)
    t3 = datetime.now() + timedelta(hours=3)
    t4 = datetime.now() + timedelta(hours=4)

    if datetime.now().strftime('%M') < str(30):
        m = str("{0:0>2}".format(0))
    elif datetime.now().strftime('%M') >= str(30):
        m = str(30)
    now = datetime.now().strftime('%-I:' + m)
    now1 = t1.strftime('%-I:' + m)
    now2 = t2.strftime('%-I:' + m)
    now3 = t3.strftime('%-I:' + m)
    now4 = t4.strftime('%-I:' + m)
    request.cls.now = now
    request.cls.now1 = now1
    request.cls.now2 = now2
    request.cls.now3 = now3
    request.cls.now4 = now4
    yield


@pytest.mark.usefixtures("setup", "directory")
class TestVersion:
    def test_version(self, onstream_version, onstream_url):
        try:
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/div[2]/span/span[2]/a/span')))  # Wait for the TV Guide Button
            self.driver.find_element(By.XPATH, '//a[@role="button"]').click()  # Click on the Settings Button
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/div[3]/span/span/span/a[1]').click()  # Click on Support
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//div[@class="_1Z4-o8_T3QF6uOX_L9JVTe"]')))  # Wait for the page to load
            v = self.driver.find_element(By.XPATH, '//p[@class="F0aslfbXZ_xrEWCBq2tyc"]')  # Find the Application Version text
            v = v.text.split(':')[1].strip()
            assert onstream_version == v
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Opera",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "timeout error"


@pytest.mark.usefixtures("setup", "directory")
class TestHomeScreen:
    def test_images_displayed(self, onstream_version, onstream_url, client_setup):
        try:
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/div[2]/span/span[2]/a/span')))  # Wait for the TV Guide Button
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]').is_displayed()  # Black Header Banner
            self.driver.find_element(By.XPATH, '//img[@alt="Dish Logo"]').is_displayed()  # Dish Logo Upper Left
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/div[1]/div[2]').is_displayed()  # Thin Line between Logos
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div').is_displayed()  # Page Background
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/div[2]/span/span[1]').is_displayed()  # underline
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[3]/div').is_displayed()  # Bottom Image
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/div[3]/span/span/a/img').is_displayed()  # Settings Cog
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/hr').is_displayed()  # Thin Line Bellow Full TV Guide Button
            live = self.driver.find_elements(By.XPATH, '//div[@class="_1acuZqkpaJBNYrvoPzBNq_ _1Ec0IteN1F_Ae9opzh37wr"]')  # Popular Channels
            custom = self.driver.find_elements(By.XPATH, '//img[@alt="' + self.logo + '"]')  # Custom Property Logo Upper Left and Centered
            for image in live:
                image.is_displayed()  # popular_channels
            for logo in custom:
                logo.is_displayed()  # Custom Property Logo Upper Left and Centered
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Opera",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "timeout error"

    def test_buttons_displayed(self, onstream_version, onstream_url, client_setup):
        try:
            self.driver.find_element(By.XPATH, '//a[contains(@href,"home")]').is_displayed()  # Home Button
            self.driver.find_element(By.XPATH, '//a[contains(@href,"epg")]').is_displayed()  # Guide Button
            self.driver.find_element(By.XPATH, '//a[@class="m6EdrAqXz3o1yv-vdZ1ZV"]').is_displayed()  # Setting Cog Button
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[1]/div/button').is_displayed()  # View Full TV Guide Button
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[3]/div/button').is_displayed()  # Learn More Button
            drop_down = self.driver.find_elements(By.XPATH, '//a[@class="_2deZevu5QMD14sqLkdr8Pc schema_accent_background_hover"]')  # Setting Cog Drop Down Buttons
            live = self.driver.find_elements(By.XPATH, '//div[@class="Y--5UdadxXiNUsObz5ATF _1-GnTrsTv-I1bU52BCijGR"]')  # Popular Channels Watch Live Button
            for button in live:
                button.is_displayed()  # Popular Channels Watch Live Button
            for button1 in drop_down:
                button1.is_displayed()  # Setting Cog Drop Down Buttons
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Opera",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "timeout error"

    def test_buttons_enabled(self, onstream_version, onstream_url, client_setup):
        try:
            self.driver.find_element(By.XPATH, '//a[contains(@href,"home")]').is_enabled()  # Home Button
            self.driver.find_element(By.XPATH, '//a[contains(@href,"epg")]').is_enabled()  # Guide Button
            self.driver.find_element(By.XPATH, '//a[@class="m6EdrAqXz3o1yv-vdZ1ZV"]').is_enabled()  # Setting Cog Button
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[1]/div/button').is_enabled()  # View Full TV Guide Button
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[3]/div/button').is_enabled()  # Learn More Button
            drop_down = self.driver.find_elements(By.XPATH, '//a[@class="_2deZevu5QMD14sqLkdr8Pc schema_accent_background_hover"]')  # Setting Cog Drop Down Buttons
            live = self.driver.find_elements(By.XPATH, '//div[@class="Y--5UdadxXiNUsObz5ATF _1-GnTrsTv-I1bU52BCijGR"]')  # Popular Channels Watch Live Button
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
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Opera",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "timeout error"

    def test_text_displayed(self, onstream_version, onstream_url, client_setup):
        try:
            self.driver.find_element(By.XPATH, '//span[contains(text(), "Home")]')  # Home
            self.driver.find_element(By.XPATH, '//span[contains(text(), "TV Guide")]')  # TV Guide
            self.driver.find_element(By.XPATH, '//button[contains(text(), "VIEW FULL TV GUIDE")]')  # View Full TV Guide
            self.driver.find_element(By.XPATH, '//div[contains(text(), "Most Popular Channels")]')  # Most Popular Channels
            self.driver.find_element(By.XPATH, '//div[contains(text(), "Want more channels, a DVR, or additional features?")]')  # Questions
            self.driver.find_element(By.XPATH, '//div[contains(text(), "Call 866-794-6166")]')  # Phone Number
            live = self.driver.find_elements(By.XPATH, '//div[@class="_1MhUC88bcyh64jOZVIlotn _3DE_w36fN1va108RdAiaue" and text()="WATCH TV"]')  # Watch TV
            for text in live:
                text.is_displayed()  # Watch TV
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Opera",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "timeout error"

    def test_link_clickable(self, onstream_version, onstream_url, client_setup):
        try:
            learn_more = self.driver.find_element(By.XPATH, '//button[@class="_3bVSq8WuOfkHK9axvntlpN null"]')  # Learn More
            self.driver.execute_script('arguments[0].scrollIntoView(true);', learn_more)  # Scroll Down to the Bottom
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//button[@class="_3bVSq8WuOfkHK9axvntlpN null"]'))).click()  # Learn More
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
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Opera",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "timeout error"


@pytest.mark.usefixtures("setup", "directory", "current_time")
class TestGuideScreen:
    def test_images_displayed(self, first_channel, all_guide_uid, onstream_version, onstream_url, client_setup):
        try:
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/div[2]/span/span[2]/a/span'))).click()  # Click on the Guide Button
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[2]/div/div/div/div[1]/div[1]')))  # Wait for the TODAY text to appear
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="%s"]' % first_channel)))  # Verify Guide Data is loaded
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]').is_displayed()  # Black Header Banner
            self.driver.find_element(By.XPATH, '//img[@alt="Dish Logo"]').is_displayed()  # Dish Logo Upper Left
            self.driver.find_element(By.XPATH, '//img[@alt="' + self.logo + '"]').is_displayed()  # Custom Property Logo Upper Left
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/div[1]/div[2]').is_displayed()  # Thin Line between Logos
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[1]').is_displayed()  # Top White Line
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[2]/div/div/div/div[2]/div[3]/div').is_displayed()  # vertical bar
            logos = self.driver.find_elements(By.XPATH, '//img[@class="_2taHIt9ptBC9h3nyExFgez"]')  # Channel Logos
            if len(logos) == len(active_service):
                assert True  # Number of Logos is the same as the number of channels
            else:
                assert False
            for gu in all_guide_uid:  # A for loop which compares the list of JSON data with the list of Guide Data in OnStream
                for logo in all_ld:
                    if str(logo['suid']) in str(gu):
                        assert True
            for a in active_service:  # A for loop which compares the list of JSON data with the list of Guide Data in OnStream (CallLetters)
                for logo in all_ld:
                    if str(logo['callsign']) in str(a):
                        assert True
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Opera",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "timeout error"

    def test_text_displayed(self, onstream_version, onstream_url, client_setup):
        try:
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[2]/div/div/div/div[1]/div[1]').is_displayed()  # TODAY
            self.driver.find_element(By.XPATH, '//div[contains(text(), "%s")]' % self.now).is_displayed()  # Current Time
            self.driver.find_element(By.XPATH, '//div[contains(text(), "%s")]' % self.now1).is_displayed()  # Time 1
            self.driver.find_element(By.XPATH, '//div[contains(text(), "%s")]' % self.now2).is_displayed()  # Time 2
            self.driver.find_element(By.XPATH, '//div[contains(text(), "%s")]' % self.now3).is_displayed()  # Time 3
            self.driver.find_element(By.XPATH, '//span[contains(text(), "MORE INFO")]').is_displayed()  # More Info
            self.driver.find_element(By.XPATH, '//span[contains(text(), "WATCH LIVE")]').is_displayed()  # Watch Live
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Opera",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "timeout error"

    def test_buttons_displayed(self, onstream_version, onstream_url, client_setup):
        try:
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[2]/div/div/div/div[2]/div[1]/div/div[1]/button/div[2]').is_displayed()  # Right Arrow
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[2]/div/div/div/div[2]/div[1]/div/div[2]/div/div/div[1]/div/div[1]/div/div/div[1]/div/div/div/div[2]/a').is_displayed()  # Play Button
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[2]/div/div/div/div[2]/div[1]/div/div[2]/div/div/div[1]/div/div[1]/div/div/div[1]/div/div/div/div[1]/div[2]').is_displayed()  # More Info Button
            self.driver.find_element(By.XPATH, '//a[contains(@href,"home")]').is_displayed()  # Home Button
            self.driver.find_element(By.XPATH, '//a[@class="m6EdrAqXz3o1yv-vdZ1ZV"]').is_displayed()  # Setting Cog Button
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Opera",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "timeout error"

    def test_buttons_clickable(self, onstream_version, onstream_url, client_setup):
        try:
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[2]/div/div/div/div[2]/div[1]/div/div[1]/button/div[2]').is_enabled()  # Right Arrow
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[2]/div/div/div/div[2]/div[1]/div/div[2]/div/div/div[1]/div/div[1]/div/div/div[1]/div/div/div/div[2]/a').is_enabled()  # Play Button
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[2]/div/div/div/div[2]/div[1]/div/div[2]/div/div/div[1]/div/div[1]/div/div/div[1]/div/div/div/div[1]/div[2]').is_enabled()  # More Info Button
            self.driver.find_element(By.XPATH, '//a[contains(@href,"home")]').is_enabled()  # Home Button
            self.driver.find_element(By.XPATH, '//a[@class="m6EdrAqXz3o1yv-vdZ1ZV"]').is_enabled()  # Setting Cog Button
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Opera",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "timeout error"

    def test_guide_function(self, onstream_version, onstream_url, client_setup):
        try:
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[2]/div/div/div/div[2]/div[1]/div/div[1]/button/div[2]'))).click()  # Click on the Right Arrow
            WebDriverWait(self.driver, 30).until_not(ec.visibility_of_element_located((By.XPATH, '//div[contains(text(), "%s")]' % self.now)))  # Make Sure the Current Time is not Visible
            self.driver.find_element(By.XPATH, '//div[contains(text(), "%s")]' % self.now4).is_displayed()  # Time 4
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[2]/div/div/div/div[2]/div[1]/div/div[1]/button[2]/div[2]'))).click()  # Click on the Left Arrow
            self.driver.find_element(By.XPATH, '//div[contains(text(), "%s")]' % self.now).is_displayed()  # Current Time
            logos = self.driver.find_elements(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[2]/div/div/div/div[2]/div[3]/div/div/div[1]/div/img')  # Channel Logos
            logo = []  # Store the Logo Channel Numbers
            for i in range(len(logos)):  # Collect all the Logo Channel Numbers
                logo.append(logos[i].get_attribute("alt"))
            last_logo = self.driver.find_element(By.XPATH, '//img[@alt="%s"]' % str(logo[-1]))  # Last Logo
            first_logo = self.driver.find_element(By.XPATH, '//img[@alt="%s"]' % str(logo[0]))  # First Logo
            self.driver.execute_script('arguments[0].scrollIntoView(true);', last_logo)  # Scroll to Bottom of Guide
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="%s"]' % str(logo[-1]))))  # Make Sure the Last Channel Logo is visible
            self.driver.execute_script('arguments[0].scrollIntoView(true);', first_logo)  # Scroll to Top of Guide
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="%s"]' % str(logo[0]))))  # Make Sure the First Channel Logo is visible
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Opera",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "timeout error"


@pytest.mark.usefixtures("setup", "directory", "current_time")
class TestSideBarScreen:
    def test_images_displayed(self, onstream_url, onstream_version, first_channel, call_letters, all_guide_uid, client_setup):
        try:
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/div[2]/span/span[2]/a/span'))).click()  # Click on the Guide Button
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[2]/div/div/div/div[1]/div[1]')))  # Wait for the TODAY text to appear
            channel = self.driver.find_elements(By.XPATH, '//div[@class="_1oYG-YxQjfR03e0opQbNNC"]')  # click on first channel More Info button
            for i in range(100):
                try:
                    channel[i].click()
                    if WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="%s"]' % call_letters))):  # wait for first channel image to appear
                        break
                    else:
                        WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, '//button[@class="_1Xyb-h8ETwWmEllf3HIy58"]'))).click()  # click back button
                        WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="%s"]' % first_channel)))  # wait for the guide to populate
                        pass
                except TimeoutException:
                    button = self.driver.find_elements(By.XPATH, '//div[@class="JuHZzfNzpm4bD3481WYQW jEGIqrEa7SjV1rD7HxHBc"]')
                    if len(button) == 1:  # see if exit button is there
                        WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, '//button[@class="_1Xyb-h8ETwWmEllf3HIy58"]'))).click()  # click exit button
                        WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="%s"]' % first_channel)))  # wait for the guide to populate
                        pass
                    elif len(button) == 0:  # see if exit button is there
                        pass
                except NoSuchElementException:
                    if not self.driver.find_element(By.XPATH, '//button[@class="_1Xyb-h8ETwWmEllf3HIy58"]'):  # see if exit button is there
                        pass
                    elif self.driver.find_element(By.XPATH, '//button[@class="_1Xyb-h8ETwWmEllf3HIy58"]'):  # see if exit button is there
                        WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, '//button[@class="_1Xyb-h8ETwWmEllf3HIy58"]'))).click()  # click exit button
                        WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="%s"]' % first_channel)))  # wait for the guide to populate
                        pass
                except ElementClickInterceptedException:
                    pass
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[1]/div[2]/div[1]').is_displayed()  # show picture
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[1]/div[1]').is_displayed()  # banner
            self.driver.find_element(By.XPATH, '//img[@alt="Dish Logo"]').is_displayed()  # dish
            self.driver.find_element(By.XPATH, '//img[@alt="' + self.logo + '"]').is_displayed()  # Custom Property Logo Upper Left
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/div[1]/div[2]').is_displayed()  # Thin Line between Logos
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[1]').is_displayed()  # Top White Line
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[2]/div/div/div/div[2]/div[3]/div').is_displayed()  # vertical bar
            logos = self.driver.find_elements(By.XPATH, '//img[@class="_2taHIt9ptBC9h3nyExFgez"]')  # Channel Logos
            if len(logos) == len(active_service):
                assert True  # Number of Logos is the same as the number of channels
            else:
                assert False
            side_channel_logo = self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[1]/div[1]/div/img')  # channel logo in side bar
            assert side_channel_logo.get_attribute("alt") == call_letters
            for gu in all_guide_uid:  # A for loop which compares the list of JSON data with the list of Guide Data in OnStream
                for logo in all_ld:
                    if str(logo['suid']) in str(gu):
                        assert True
            for a in active_service:  # A for loop which compares the list of JSON data with the list of Guide Data in OnStream (CallLetters)
                for logo in all_ld:
                    if str(logo['callsign']) in str(a):
                        assert True
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Opera",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "timeout error"

    def test_text_displayed(self, onstream_url, onstream_version, client_setup):
        try:
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[1]/div[2]/div[2]/div[1]').is_displayed()  # Program Title
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[1]/div[2]/div[2]/div[2]').is_displayed()  # Episode Information
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[1]/div[2]/div[2]/div[3]').is_displayed()  # Episode Run-Time
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[1]/div[2]/div[2]/div[4]').is_displayed()  # Episode Description
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[2]/div/div/div/div[1]/div[1]').is_displayed()  # TODAY
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
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Opera",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "timeout error"

    def test_buttons_displayed(self, onstream_url, onstream_version, client_setup):
        try:
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[1]/div[1]/button').is_displayed()  # exit button
            self.driver.find_element(By.XPATH, '//span[contains(text(), "WATCH LIVE")]').is_displayed()  # Watch Live
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[2]/div/div/div/div[2]/div[1]/div/div[2]/div/div/div[1]/div/div[1]/div/div/div[2]/div/div/div/div[1]/div[2]').is_displayed()  # more info button
            self.driver.find_element(By.XPATH, '//a[contains(@href,"home")]').is_displayed()  # home button
            self.driver.find_element(By.XPATH, '//a[@class="m6EdrAqXz3o1yv-vdZ1ZV"]').is_displayed()  # Setting Cog Button
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Opera",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "timeout error"

    def test_buttons_clickable(self, onstream_url, onstream_version, client_setup):
        try:
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[1]/div[1]/button').is_enabled()  # exit button
            self.driver.find_element(By.XPATH, '//span[contains(text(), "WATCH LIVE")]').is_enabled()  # Watch Live
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[2]/div/div/div/div[2]/div[1]/div/div[2]/div/div/div[1]/div/div[1]/div/div/div[2]/div/div/div/div[1]/div[2]').is_enabled()  # more info button
            self.driver.find_element(By.XPATH, '//a[contains(@href,"home")]').is_enabled()  # home button
            self.driver.find_element(By.XPATH, '//a[@class="m6EdrAqXz3o1yv-vdZ1ZV"]').is_enabled() # Setting Cog Button
            self.driver.find_element(By.XPATH, '//span[contains(text(), "WATCH LIVE")]').click()  # Watch Live
            WebDriverWait(self.driver, 30).until_not(ec.presence_of_element_located((By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')))
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Opera",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "timeout error"


@pytest.mark.usefixtures("setup", "directory", "current_time")
class TestLiveTV:
    def test_images_displayed(self, onstream_url, onstream_version, first_channel, call_letters, client_setup):
        try:
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/div[2]/span/span[2]/a/span'))).click()  # Click on the Guide Button
            WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="%s"]' % first_channel)))  # Wait For the Guide to Populate
            channel = self.driver.find_elements(By.XPATH, '//div[@class="_3oY1sebpEJCA1_vGf8PEBX"]')  # Get a List of all the Current Programs Play Buttons
            for i in range(100):  # Go through that list of Programs and Select the Play button for them
                try:
                    channel[i].click()
                    if WebDriverWait(self.driver, 10).until(ec.presence_of_element_located((By.XPATH, '//img[@alt="%s"]' % call_letters))):  # wait for first channel image to appear
                        break  # Break the Loop if the Program selected is the correct one
                    else:  # If the Program was not the correct one, continue the for loop
                        WebDriverWait(self.driver, 10).until(ec.presence_of_element_located((By.XPATH, '//span[contains(text(), "FULL TV GUIDE")]'))).click()  # click back button
                        WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="%s"]' % first_channel)))  # wait for the guide to populate
                        pass
                except TimeoutException:
                    button = self.driver.find_elements(By.XPATH, '//div[@class="JuHZzfNzpm4bD3481WYQW jEGIqrEa7SjV1rD7HxHBc"]')
                    if len(button) == 1:  # see if exit button is there
                        WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, '//button[@class="_1Xyb-h8ETwWmEllf3HIy58"]'))).click()  # click exit button
                        WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="%s"]' % first_channel)))  # wait for the guide to populate
                        pass
                    elif len(button) == 0:  # see if exit button is there
                        pass
                except NoSuchElementException:
                    if not self.driver.find_element(By.XPATH, '//button[@class="_1Xyb-h8ETwWmEllf3HIy58"]'):  # see if exit button is there
                        pass
                    elif self.driver.find_element(By.XPATH, '//button[@class="_1Xyb-h8ETwWmEllf3HIy58"]'):  # see if exit button is there
                        WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, '//button[@class="_1Xyb-h8ETwWmEllf3HIy58"]'))).click()  # click exit button
                        WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="%s"]' % first_channel)))  # wait for the guide to populate
                        pass
                except ElementClickInterceptedException:
                    pass
                except ElementNotInteractableException:
                    pass
            WebDriverWait(self.driver, 30).until_not(ec.presence_of_element_located((By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')))  # Wait for the loading screen to disappear
            time.sleep(3)
            self.driver.refresh()
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//button[@class="h2xyENO_W_yt024oi0MrN"]'))).is_enabled()
            self.driver.find_element(By.XPATH, '//button[@class="h2xyENO_W_yt024oi0MrN"]').click()
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//img[@id="bmpui-id-32"]')))  # Wait for the LiveTV to Start
            self.driver.find_element(By.XPATH, '//span[@class="bmpui-ui-label bmpui-miniEpgToggleLabel"]').click()  # click on the mini guide
            self.driver.find_element(By.XPATH, '//div[@class="bmpui-container-wrapper"]').is_displayed()  # Channel logo top right
            self.driver.find_element(By.XPATH, '//img[@alt="%s"]' % call_letters).is_displayed()  # Channel logo in mini guide
            self.driver.find_element(By.XPATH, '//div[@class="bmpui-ui-container bmpui-divider"]').is_displayed()  # divider
            self.driver.find_element(By.XPATH, '//div[@class="bmpui-ui-container bmpui-fullTvGuideIcon"]').is_displayed()  # Left Arrow
            self.driver.find_element(By.XPATH, '//span[@class="bmpui-ui-label bmpui-miniEpgToggleLabel"]').is_displayed()  # Down Arrow
            self.driver.find_element(By.XPATH, '//div[@class="_2ce79Sw43-fKTd_hNeR50P"]').is_displayed()  # Right Arrow
            self.driver.find_element(By.XPATH, '//div[@class="bmpui-ui-container bmpui-moreInfoIcon"]').is_displayed()  # info emblem
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Opera",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "timeout error"

    def test_text_displayed(self, onstream_url, onstream_version, client_setup):
        try:
            self.driver.find_element(By.XPATH, '//*[@id="dish-campustv-player"]/div[4]/div/div/div/div/div[1]/div[1]').is_displayed()  # TODAY
            self.driver.find_element(By.XPATH, '//div[contains(text(), "%s")]' % self.now).is_displayed()  # Time 1
            self.driver.find_element(By.XPATH, '//div[contains(text(), "%s")]' % self.now1).is_displayed()  # Time 2
            self.driver.find_element(By.XPATH, '//div[contains(text(), "%s")]' % self.now2).is_displayed()  # Time 3
            self.driver.find_element(By.XPATH, '//div[contains(text(), "%s")]' % self.now3).is_displayed()  # Time 4
            self.driver.find_element(By.XPATH, '//span[@class="bmpui-ui-label bmpui-title"]').is_displayed()  # Show title
            self.driver.find_element(By.XPATH, '//span[@class="bmpui-ui-label bmpui-subTitle"]').is_displayed()  # Show episode
            self.driver.find_element(By.XPATH, '//span[text()="FULL TV GUIDE"]').is_displayed()  # Full TV Guide
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
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Opera",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "timeout error"

    def test_buttons_displayed(self, onstream_url, onstream_version, client_setup):
        try:
            self.driver.find_element(By.XPATH, '//div[@class="bmpui-ui-container bmpui-fullTvGuideIcon"]').is_displayed()  # Full TV Guide back button
            self.driver.find_element(By.XPATH, '//div[@class="bmpui-ui-container bmpui-moreInfoIcon"]').is_displayed()  # More Info button
            self.driver.find_element(By.XPATH, '//span[@class="bmpui-ui-label bmpui-miniEpgToggleLabel"]').is_displayed()  # Mini Guide down button
            self.driver.find_element(By.XPATH, '//*[@id="dish-campustv-player"]/div[4]/div/div/div/div/div[2]/div[1]/div/div[1]/button/div[2]').is_displayed()  # Mini Guide right arrow button
            self.driver.find_element(By.XPATH, '//*[@id="dish-campustv-player"]/div[4]/div/div/div/div/div[2]/div[1]/div/div[2]/div/div/div[1]/div/div[1]/div/div/div[1]/div/div/div/div[1]/div[2]').is_displayed()  # Mini Guide More Info button
            self.driver.find_element(By.XPATH, '//*[@id="dish-campustv-player"]/div[4]/div/div/div/div/div[2]/div[1]/div/div[2]/div/div/div[1]/div/div[1]/div/div/div[1]/div/div/div/div[2]/a').is_displayed()  # play button
            self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-volumetogglebutton bmpui-unmuted"]').is_displayed()  # Mute button
            self.driver.find_element(By.XPATH, '//div[@class="bmpui-seekbar-markers"]').is_displayed()  # Seeker Bar
            """self.driver.find_element_by_xpath('//div[@class="bmpui-seekbar-playbackposition-marker schema_accent_background"]').is_displayed()"""  # Seeker Bar Dot
            self.driver.find_element(By.XPATH, '//button[@id="bmpui-id-18"]').is_displayed()  # Cast button
            self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-cctogglebutton bmpui-off"]').is_displayed()  # Closed Caption button
            self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-fullscreentogglebutton bmpui-off"]').is_displayed()  # Full Screen button
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Opera",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "timeout error"

    def test_buttons_enabled(self, onstream_url, onstream_version, client_setup):
        try:
            self.driver.find_element(By.XPATH, '//div[@class="bmpui-ui-container bmpui-fullTvGuideIcon"]').is_enabled()  # Full TV Guide back button
            self.driver.find_element(By.XPATH, '//div[@class="bmpui-ui-container bmpui-moreInfoIcon"]').is_enabled()  # More Info button
            self.driver.find_element(By.XPATH, '//span[@class="bmpui-ui-label bmpui-miniEpgToggleLabel"]').is_enabled()  # Mini Guide down button
            self.driver.find_element(By.XPATH, '//*[@id="dish-campustv-player"]/div[4]/div/div/div/div/div[2]/div[1]/div/div[1]/button/div[2]').is_enabled()  # Mini Guide right arrow button
            self.driver.find_element(By.XPATH, '//*[@id="dish-campustv-player"]/div[4]/div/div/div/div/div[2]/div[1]/div/div[2]/div/div/div[1]/div/div[1]/div/div/div[1]/div/div/div/div[1]/div[2]').is_enabled()  # Mini Guide More Info button
            self.driver.find_element(By.XPATH, '//*[@id="dish-campustv-player"]/div[4]/div/div/div/div/div[2]/div[1]/div/div[2]/div/div/div[1]/div/div[1]/div/div/div[1]/div/div/div/div[2]/a').is_enabled()  # play button
            self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-volumetogglebutton bmpui-unmuted"]').is_enabled()  # Mute button
            self.driver.find_element(By.XPATH, '//div[@class="bmpui-seekbar-markers"]').is_enabled()  # Seeker Bar
            """self.driver.find_element_by_xpath('//div[@class="bmpui-seekbar-playbackposition-marker schema_accent_background"]').is_enabled()"""  # Seeker Bar Dot
            self.driver.find_element(By.XPATH, '//button[@id="bmpui-id-18"]').is_enabled()  # Cast button
            self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-cctogglebutton bmpui-off"]').is_enabled()  # Closed Caption button
            self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-fullscreentogglebutton bmpui-off"]').is_enabled()  # Full Screen button
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Opera",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "timeout error"

    def test_control_bar_functions(self, onstream_url, onstream_version, client_setup):
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
            if WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '(//div[@aria-valuenow="55"])'))):
                assert True
            else:
                assert False, "Volume did not increase on the slider volume bar"
            #  turn full screen off and on
            self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-fullscreentogglebutton bmpui-off"]').click()  # turn full screen on
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//button[@class="bmpui-ui-fullscreentogglebutton bmpui-on"]')))  # full screen on
            self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-fullscreentogglebutton bmpui-on"]').click()  # turn full screen off
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//button[@class="bmpui-ui-fullscreentogglebutton bmpui-off"]')))  # full screen off
            # turn CC button off and on
            if WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//button[@class="bmpui-ui-cctogglebutton bmpui-off"]'))):
                WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                    (By.XPATH, '//button[@class="bmpui-ui-cctogglebutton bmpui-off"]'))).click()  # CC button turn on
                WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located(
                    (By.XPATH, '//button[@class="bmpui-ui-cctogglebutton bmpui-on"]')))  # CC button on
                WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                    (By.XPATH, '//button[@class="bmpui-ui-cctogglebutton bmpui-on"]'))).click()  # CC button turn off
                self.driver.find_element(By.XPATH,
                                         '//button[@class="bmpui-ui-cctogglebutton bmpui-off"]').is_displayed()  # CC button off
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
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Opera",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "timeout error"


@pytest.mark.usefixtures("setup", "directory")
class TestSupportSettingsScreen:
    def test_images_displayed(self, onstream_url, onstream_version, client_setup):
        try:
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/div[2]/span/span[2]/a/span')))  # Wait for the TV Guide Button
            self.driver.find_element(By.XPATH, '//a[@role="button"]').click()  # Click on the Settings Button
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/div[3]/span/span/span/a[1]').click()  # Click on Support
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//div[@class="_1Z4-o8_T3QF6uOX_L9JVTe"]')))  # Wait for the page to load
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[1]/div/div/div[1]/div/div').is_displayed()
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Opera",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "timeout error"

    def test_text_displayed(self, onstream_url, onstream_version, client_setup):
        try:
            self.driver.find_element(By.XPATH, '//h2[contains(text(), "Frequently Asked Questions")]').is_displayed()  # Freq asked questions
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//p[contains(text(), "How can I watch OnStream?")]')))  # How can I watch OnStream
            """self.driver.find_element_by_xpath('//p[contains(text(), "How can I watch OnStream?")]').is_displayed()"""
            """self.driver.find_element_by_xpath('//p[contains(text(), "What devices are supported by OnStream? - Claudio’s Test")]').is_displayed()"""  # suported devices
            self.driver.find_element(By.XPATH, '//p[contains(text(), "When I leave my property why do I lose access to OnStream?")]').is_displayed()  # additional channels
            self.driver.find_element(By.XPATH, '//p[contains(text(), "What internet speed do I need to be able to use OnStream?")]').is_displayed()  # who to contact
            self.driver.find_element(By.XPATH, '//p[contains(text(), "What Channels does OnStream have?")]').is_displayed()  # how to cast
            self.driver.find_element(By.XPATH, '//p[contains(text(), "Are all channels live?")]').is_displayed()  # when I leave
            """self.driver.find_element_by_xpath('//p[contains(text(), "Can’t find the answer to what you’re looking for?")]').is_displayed()"""  # can't find answers
            """self.driver.find_element_by_xpath('//p[contains(text(), "Please Call Dish Support at: ")]').is_displayed()  # call dish support
            self.driver.find_element_by_xpath('//p[contains(text(), "1-800-333-DISH")]').is_displayed()"""  # number to call
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Opera",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "timeout error"


@pytest.mark.usefixtures("setup", "directory")
class TestLegalSettingsScreen:
    def test_images_displayed(self, onstream_url, onstream_version, client_setup):
        try:
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/div[2]/span/span[2]/a/span')))  # Wait for the TV Guide Button
            self.driver.find_element(By.XPATH, '//a[@role="button"]').click()  # Click on the Settings Button
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/div[3]/span/span/span/a[2]').click()  # Click on the Legal Button
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[1]/div/div')))  # Wait for the page to load
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[1]/div/div/div[1]/div/div').is_displayed()
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Opera",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "timeout error"

    def test_text_displayed(self, onstream_url, onstream_version, client_setup):
        try:
            self.driver.find_element(By.XPATH, '//h2[contains(text(), "Legal")]').is_displayed()  # Legal
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//h4[contains(text(), "Service Agreement")]')))
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//h4[contains(text(), "Terms and Conditions")]')))
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Opera",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "timeout error"

    def test_link1_clickable(self, onstream_url, onstream_version, client_setup):
        try:
            self.driver.find_element(By.XPATH, '//a[@href="https://www.dish.com/service-agreements/"]').click()
            self.driver.find_element(By.XPATH, '//h1[contains(text(), "DISH Network Service Agreements")]').is_displayed()
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Opera",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write_points(body)
            assert False, "Element was not found"
        except TimeoutException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            loading_circle = self.driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = self.driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = self.driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = self.driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "timeout error"

    def test_link2_clickable(self, onstream_url, onstream_version, client_setup):
        try:
            self.driver.get(self.dishtv)
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/div[2]/span/span[2]/a/span')))  # Wait for the TV Guide Button
            self.driver.find_element(By.XPATH, '//a[@role="button"]').click()  # Click on the Settings Button
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/div[3]/span/span/span/a[2]').click()  # Click on the Legal Button
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[1]/div/div')))  # Wait for the page to load
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//a[@href="https://www.dish.com/terms-conditions/"]'))).click()
            """self.driver.find_element(By.XPATH, '//a[@href="https://www.dish.com/terms-conditions/"]').click()"""
            self.driver.find_element(By.XPATH, '//h1[contains(text(), "Important Terms and Conditions")]').is_displayed()
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Opera",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write_points(body)
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
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "timeout error"


@pytest.mark.usefixtures("setup", "directory", "current_time")
class TestServices:
    def test_services_configured(self, onstream_url, onstream_version, client_setup, first_channel):
        try:
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/div[2]/span/span[2]/a/span'))).click()  # Click on the Guide Button
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[2]/div/div/div/div[1]/div[1]')))  # Wait for the TODAY text to appear
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="%s"]' % first_channel)))  # Verify Guide Data is loaded
            links = []
            channels = self.driver.find_elements(By.XPATH, '//a[@class="_2eB_OXy4vbP1Kd9moNzO4j"]')  # Get the Video Player Classes
            for i in range(len(channels)):
                links.append(channels[i].get_attribute("href"))
            all_channels = list(dict.fromkeys(links))
            for link in all_channels:
                channel = link.strip().split('/')[5]
                self.driver.get(link)
                self.driver.refresh()
                try:
                    if WebDriverWait(self.driver, 10).until(ec.presence_of_element_located((By.XPATH, '//button[@class="h2xyENO_W_yt024oi0MrN"]'))).is_enabled():
                        self.driver.find_element(By.XPATH, '//button[@class="h2xyENO_W_yt024oi0MrN"]').click()
                    else:
                        pass
                except TimeoutException:
                    pass
                WebDriverWait(self.driver, 30).until_not(ec.visibility_of_element_located((By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')))
                WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//div[@class="bitmovinplayer-poster"]')))
                time.sleep(5)
                self.driver.save_screenshot(self.direct + str(channel) + ".png")
        except NoSuchElementException:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": onstream_version,
                        "Test": 1,
                        "Pytest": self.name,
                        "URL": onstream_url,
                        "Browser": "Opera",
                        "Device": device,
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "element_not_found": 1,
                    }
                }
            ]
            client_setup.write_points(body)
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
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "loading_circle": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck on loading screen"
            elif len(no_streaming) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "unable_to_connect": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "It appears that you are not able to connect to Streaming Services at this time."
            elif len(error_404) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "error_404": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "404 error"
            elif len(loading_element):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "element_loading": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Stuck loading an element"
            elif len(went_wrong):
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "went_wrong": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "Something went wrong"
            else:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": onstream_version,
                            "Test": 1,
                            "Pytest": self.name,
                            "URL": onstream_url,
                            "Browser": "Opera",
                            "Device": device,
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client_setup.write_points(body)
                assert False, "timeout error"
