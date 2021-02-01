import os
import subprocess
import pytest
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
from iPhone_Safari_Thread import version, mc, ChannelCount, device, active_service, all_ld

testrun = '2.0.4'

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
    elif datetime.now().strftime('%M') >= str(30):
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
    dishtv = ChannelCount.dishtv
    desired_caps = ChannelCount.desired_caps
    driver = webdriver.Remote('http://localhost:4723/wd/hub', desired_caps)
    driver.get(dishtv)
    request.cls.driver = driver
    logo = "DaVita Logo"  # Big logo on home screen
    request.cls.logo = logo
    request.cls.dishtv = dishtv
    yield
    driver.quit()


@pytest.mark.usefixtures("setup", "directory")
class TestVersion:
    def test_version(self):
        try:
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/span/button/div'))).click()  # Click on the Hamburger
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//span[contains(text(), "Settings")]'))).click()  # Click on the Settings button
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//*[@id="react-tabs-0"]')))  # Wait for the page to load
            v = self.driver.find_element(By.XPATH, '//*[@id="react-tabs-1"]/div/div/p')  # Version Number
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
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/span/button/div')))  # Wait for the page to load
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]').is_displayed()  # Top black banner
            self.driver.find_element(By.XPATH, '//img[@alt="Dish Logo"]').is_displayed()  # dish
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/div[1]/div[2]').is_displayed()  # Thin Line between Logos
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div').is_displayed()  # Page Background
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/div[2]/span/span[1]').is_displayed()  # underline
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[3]/div').is_displayed()  # Bottom Image
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/span/button/div').is_displayed()  # Hamburger
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
                        "Software": version,
                        "Test": mc.get_value(),
                        "Pytest": self.name,
                        "URL": ChannelCount.dishtv,
                        "Browser": "Safari",
                        "Device": device,
                        
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
                        "Software": version,
                        "Test": mc.get_value(),
                        "Pytest": self.name,
                        "URL": ChannelCount.dishtv,
                        "Browser": "Safari",
                        "Device": device,
                        
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
                        "Software": version,
                        "Test": mc.get_value(),
                        "Pytest": self.name,
                        "URL": ChannelCount.dishtv,
                        "Browser": "Safari",
                        "Device": device,
                        
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
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//button[@class="_3bVSq8WuOfkHK9axvntlpN null"]')))  # learn more
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
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/span/button/div'))).click()  # Click on the Hamburger
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//span[contains(text(), "TV Guide")]'))).click()  # Click on the TV Guide button
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="%s"]' % ChannelCount.first_channel)))  # Wait for the Guide to load
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
            for gu in ChannelCount.all_guide_uid:  # A for loop which compares the list of JSON data with the list of Guide Data in OnStream
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
                        "Software": version,
                        "Test": mc.get_value(),
                        "Pytest": self.name,
                        "URL": ChannelCount.dishtv,
                        "Browser": "Safari",
                        "Device": device,
                        
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
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[2]/div/div/div/div[1]/div[1]').is_displayed()  # TODAY
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
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/span/button/div').is_displayed()  # Hamburger
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
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/span/button/div').is_enabled()  # Setting Cog
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
                            
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "timeout error"

    def test_guide_function(self):
        try:
            self.driver.execute_script("mobile: swipe", {'direction': 'left'})  # Swipe to the right
            WebDriverWait(self.driver, 30).until_not(ec.visibility_of_element_located((By.XPATH, '//div[contains(text(), "%s")]' % self.now)))  # Make Sure the Current Time is not Visible
            self.driver.find_element(By.XPATH, '//div[contains(text(), "%s")]' % self.now2).is_displayed()  # Time 3
            self.driver.execute_script("mobile: swipe", {'direction': 'right'})  # Swipe to the left
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
                        "Software": version,
                        "Test": mc.get_value(),
                        "Pytest": self.name,
                        "URL": ChannelCount.dishtv,
                        "Browser": "Safari",
                        "Device": device,
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
            went_wrong = self.driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
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
                            "Browser": "Safari",
                            "Device": device,
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
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/span/button/div'))).click()  # Click on the Hamburger
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//span[contains(text(), "TV Guide")]'))).click()  # Click on the TV Guide button
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="%s"]' % ChannelCount.first_channel)))  # Wait for the Guide to load
            channel = self.driver.find_elements(By.XPATH, '//div[@class="_1yz4ajhuNRkxAeKT820e96"]')  # click on first channel
            for i in range(100):
                try:
                    channel[i].click()  # Select the channels in the list
                    if WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="%s"]' % ChannelCount.call_letters))):  # wait for first channel image to appear
                        break  # Break the loop if the correct channel is selected
                    else:
                        WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[1]/div[1]/button'))).click()  # click back button
                        WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="%s"]' % ChannelCount.first_channel)))  # wait for the guide to populate
                        pass
                except TimeoutException:
                    button = self.driver.find_elements(By.XPATH, '//div[@class="_10r-_3yAEd4-fj1LNbwvP8 _3JZ-2M90usbcANBXDADkyw"]')  # See if the side_screen has appeared
                    if len(button) == 1:  # Check if the side_screen has appeared, if it has do the following
                        WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[1]/div[1]/button'))).click()  # click exit button
                        WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="%s"]' % ChannelCount.first_channel)))  # wait for the guide to populate
                        pass
                    elif len(button) == 0:  # Check if the side_screen has appeared, if it has do the following
                        pass
                except NoSuchElementException:
                    if not self.driver.find_element(By.XPATH, '//div[@class="_10r-_3yAEd4-fj1LNbwvP8 _3JZ-2M90usbcANBXDADkyw"]'):  # Check if the side_screen has appeared, if it has do the following
                        pass
                    elif self.driver.find_element(By.XPATH, '//div[@class="_10r-_3yAEd4-fj1LNbwvP8 _3JZ-2M90usbcANBXDADkyw"]'):  # Check if the side_screen has appeared, if it has do the following
                        WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[1]/div[1]/button'))).click()  # click exit button
                        WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="%s"]' % ChannelCount.first_channel)))  # wait for the guide to populate
                        pass
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="%s"]' % ChannelCount.call_letters)))
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[1]/div[2]/div[1]').is_displayed()  # show picture
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[1]/div[1]').is_displayed()  # banner
            side_channel_logo = self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[1]/div[1]/div/img')  # channel logo in side bar
            assert side_channel_logo.get_attribute("alt") == ChannelCount.call_letters
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
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[1]/div[2]/div[2]/div[1]').is_displayed()  # Program Title
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[1]/div[2]/div[2]/div[2]').is_displayed()  # Episode Information
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[1]/div[2]/div[2]/div[3]').is_displayed()  # Episode Run-Time
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[1]/div[2]/div[2]/div[4]').is_displayed()  # Episode Description
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
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[1]/div[1]/button').is_displayed()  # exit button
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
            self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[1]/div[1]/button').is_enabled()  # exit button
            self.driver.find_element(By.XPATH, '//span[contains(text(), "WATCH LIVE")]').is_enabled()  # Watch Live
            self.driver.find_element(By.XPATH, '//span[contains(text(), "WATCH LIVE")]').click()  # Watch Live
            WebDriverWait(self.driver, 30).until_not(ec.presence_of_element_located((By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')))  # Wait for loading screen to disappear
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
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/span/button/div'))).click()  # Click on the Hamburger
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//span[contains(text(), "TV Guide")]'))).click()  # Click on the TV Guide button
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="%s"]' % ChannelCount.first_channel)))  # Wait for the Guide to load
            channel = self.driver.find_elements(By.XPATH, '//div[@class="_1yz4ajhuNRkxAeKT820e96"]')  # click on first channel
            for i in range(100):
                try:
                    channel[i].click()  # Select the channels in the list
                    if WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="%s"]' % ChannelCount.call_letters))):  # wait for first channel image to appear
                        break  # Break the loop if the correct channel is selected
                    else:
                        WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[1]/div[1]/button'))).click()  # click back button
                        WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="%s"]' % ChannelCount.first_channel)))  # wait for the guide to populate
                        pass
                except TimeoutException:
                    button = self.driver.find_elements(By.XPATH, '//div[@class="_10r-_3yAEd4-fj1LNbwvP8 _3JZ-2M90usbcANBXDADkyw"]')  # See if the side_screen has appeared
                    if len(button) == 1:  # Check if the side_screen has appeared, if it has do the following
                        WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[1]/div[1]/button'))).click()  # click exit button
                        WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="%s"]' % ChannelCount.first_channel)))  # wait for the guide to populate
                        pass
                    elif len(button) == 0:  # Check if the side_screen has appeared, if it has do the following
                        pass
                except NoSuchElementException:
                    if not self.driver.find_element(By.XPATH, '//div[@class="_10r-_3yAEd4-fj1LNbwvP8 _3JZ-2M90usbcANBXDADkyw"]'):  # Check if the side_screen has appeared, if it has do the following
                        pass
                    elif self.driver.find_element(By.XPATH, '//div[@class="_10r-_3yAEd4-fj1LNbwvP8 _3JZ-2M90usbcANBXDADkyw"]'):  # Check if the side_screen has appeared, if it has do the following
                        WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[1]/div[1]/button'))).click()  # click exit button
                        WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="%s"]' % ChannelCount.first_channel)))  # wait for the guide to populate
                        pass
            self.driver.find_element(By.XPATH, '//span[contains(text(), "WATCH LIVE")]').click()  # Click Watch Live
            WebDriverWait(self.driver, 10).until_not(ec.presence_of_element_located((By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')))
            WebDriverWait(self.driver, 10).until(ec.presence_of_element_located((By.XPATH, '//img[@id="bmpui-id-32"]')))  # wait for loading screen to disappear
            self.driver.find_element(By.XPATH, '//li[contains(text(), "Mini Guide")]').click()  # click on the mini guide
            WebDriverWait(self.driver, 30).until_not(ec.visibility_of_element_located((By.XPATH, '//div[contains(text(), "Loading TV Guide...")]')))  # wait for mini guide to load
            self.driver.find_element(By.XPATH, '//img[@alt="%s"]' % ChannelCount.call_letters).is_displayed()  # Channel logo top
            self.driver.find_element(By.XPATH, '//img[@alt="%s"]' % ChannelCount.first_channel).is_displayed()  # Channel logo in mini guide
            self.driver.find_element(By.XPATH, '//div[@class="bmpui-ui-container bmpui-divider"]').is_displayed()  # divider
            self.driver.find_element(By.XPATH, '//div[@class="bmpui-ui-container bmpui-fullTvGuideIcon"]').is_displayed()  # Left Arrow
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
            self.driver.find_element(By.XPATH, '//div[contains(text(), "TODAY")]').is_displayed()  # TODAY
            self.driver.find_element(By.XPATH, '//div[contains(text(), "%s")]' % self.now).is_displayed()  # Time 1
            self.driver.find_element(By.XPATH, '//div[contains(text(), "%s")]' % self.now1).is_displayed()  # Time 2
            self.driver.find_element(By.XPATH, '//div[contains(text(), "%s")]' % self.now2).is_displayed()  # Time 3
            self.driver.find_element(By.XPATH, '//div[contains(text(), "%s")]' % self.now3).is_displayed()  # Time 4
            self.driver.find_element(By.XPATH, '//li[contains(text(), "Info")]').click()  # click on the Info page
            WebDriverWait(self.driver, 10).until(ec.presence_of_element_located((By.XPATH, '//*[@id="react-tabs-1"]/div/h1')))  # Episode Name
            self.driver.find_element(By.XPATH, '//*[@id="react-tabs-1"]/div/p[1]').is_displayed()  # Season and Episode Number
            self.driver.find_element(By.XPATH, '//*[@id="react-tabs-1"]/div/p[2]').is_displayed()  # Run Time
            self.driver.find_element(By.XPATH, '//*[@id="react-tabs-1"]/div/p[3]').is_displayed()  # Info
            self.driver.find_element(By.XPATH, '//li[contains(text(), "Mini Guide")]').is_displayed()  # Mini Guide
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
            self.driver.find_element(By.XPATH, '//*[@id="playercontainer"]/div[1]/button').is_displayed()  # Full TV Guide back button
            self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-volumetogglebutton bmpui-unmuted"]').is_displayed()  # Mute button
            self.driver.find_element(By.XPATH, '//div[@class="bmpui-seekbar-markers"]').is_displayed()  # Seeker Bar
            self.driver.find_element(By.XPATH, '//button[@id="bmpui-id-18"]').is_displayed()  # Cast button
            self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-cctogglebutton bmpui-off"]').is_displayed()  # Closed Caption button
            self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-fullscreentogglebutton bmpui-off"]').is_displayed()  # Full Screen button
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
            self.driver.find_element(By.XPATH, '//*[@id="playercontainer"]/div[1]/button').is_enabled()  # Full TV Guide back button
            self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-volumetogglebutton bmpui-unmuted"]').is_enabled()  # Mute button
            self.driver.find_element(By.XPATH, '//div[@class="bmpui-seekbar-markers"]').is_enabled()  # Seeker Bar
            self.driver.find_element(By.XPATH, '//button[@id="bmpui-id-18"]').is_enabled()  # Cast button
            self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-cctogglebutton bmpui-off"]').is_enabled()  # Closed Caption button
            self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-fullscreentogglebutton bmpui-off"]').is_enabled()  # Full Screen button
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
            #  turn full screen off and on
            full_screen_on = self.driver.find_element(By.XPATH, '//span[@class="bmpui-ui-fullscreentogglebutton bmpui-off"]')  # turn full screen on
            self.driver.execute_script("arguments[0].click();", full_screen_on)
            WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, '//button[@class="bmpui-ui-fullscreentogglebutton bmpui-on"]')))  # full screen on
            full_screen_off = self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-fullscreentogglebutton bmpui-on"]')  # turn full screen off
            self.driver.execute_script("arguments[0].click();", full_screen_off)
            WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, '//button[@class="bmpui-ui-fullscreentogglebutton bmpui-off"]')))  # full screen off
            #  turn mute button off and on
            WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, '//button[@data-bmpui-volume-level-tens="10"]')))
            mute_on = self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-volumetogglebutton bmpui-unmuted"]')  # Mute button turn on
            self.driver.execute_script("arguments[0].click();", mute_on)
            WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, '//button[@class="bmpui-ui-volumetogglebutton bmpui-muted"]')))  # Mute button on
            mute_off = self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-volumetogglebutton bmpui-muted"]')  # Mute button turn off
            self.driver.execute_script("arguments[0].click();", mute_off)
            self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-volumetogglebutton bmpui-unmuted"]').is_displayed()  # Mute button off
            self.driver.refresh()
            time.sleep(5)
            WebDriverWait(self.driver, 30).until_not(ec.presence_of_element_located((By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')))
            WebDriverWait(self.driver, 10).until(ec.presence_of_element_located((By.XPATH, '//img[@id="bmpui-id-32"]')))  # wait for loading screen to disappear
            # turn CC button off and on
            time.sleep(5)
            cc_on = self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-cctogglebutton bmpui-off"]')  # CC button turn on
            self.driver.execute_script("arguments[0].click();", cc_on)
            WebDriverWait(self.driver, 10).until(ec.presence_of_element_located((By.XPATH, '//button[@class="bmpui-ui-cctogglebutton bmpui-on"]')))  # CC button turn off
            cc_off = self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-cctogglebutton bmpui-on"]')  # CC button turn on
            self.driver.execute_script("arguments[0].click();", cc_off)
            self.driver.find_element(By.XPATH, '//button[@class="bmpui-ui-cctogglebutton bmpui-off"]').is_displayed()  # CC button off
            self.driver.execute_script("arguments[0].click();", cc_on)
            if WebDriverWait(self.driver, 10).until(ec.visibility_of_element_located((By.XPATH, '//div[@class="bmpui-ui-subtitle-overlay bmpui-cea608"]'))):
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
                        "Browser": "Safari",
                        "Device": device,
                        
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
    def test_text_displayed(self):
        try:
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/span/button/div'))).click()  # Click on the Hamburger
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//span[contains(text(), "Settings")]'))).click()  # Click on the Settings button
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//*[@id="react-tabs-0"]')))  # Wait for the page to load
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//p[contains(text(), "How can I watch OnStream?")]')))  # How to
            self.driver.find_element(By.XPATH, '//p[contains(text(), "What devices are supported by OnStream?")]').is_displayed()  # What is supported
            self.driver.execute_script("mobile: swipe", {'direction': 'up'})
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//p[contains(text(), "When I leave my property why do I lose access to OnStream?")]'))).is_displayed()  # additional channels
            self.driver.find_element(By.XPATH, '//p[contains(text(), "What internet speed do I need to be able to use OnStream?")]').is_displayed()  # who to contact
            self.driver.execute_script("mobile: swipe", {'direction': 'up'})
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//p[contains(text(), "What Channels does OnStream have?")]'))).is_displayed()  # What does Onstream have
            self.driver.find_element(By.XPATH, '//p[contains(text(), "Are all channels live?")]').is_displayed()  # LiveTV
            self.driver.find_element(By.XPATH, '//p[contains(text(), "Does OnStream have local channels?")]').is_displayed()  # Locals
            self.driver.execute_script("mobile: swipe", {'direction': 'up'})
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//p[contains(text(), "How do I get additional channels?")]'))).is_displayed()  # Additional Channels
            self.driver.find_element(By.XPATH, '//p[contains(text(), "How do I cast to a TV?")]').is_displayed()  # How to cast
            self.driver.find_element(By.XPATH, '//p[contains(text(), "I have access to OnStream service but am having an issue?")]').is_displayed()  # Issues
            self.driver.execute_script("mobile: swipe", {'direction': 'up'})
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//p[contains(text(), "Video and audio are out of sync")]'))).is_displayed()  # Video and Audio Issues
            self.driver.find_element(By.XPATH, '//p[contains(text(), "My Closed Captions Are Broken Or Incorrect, What Do I Do?")]').is_displayed()  # CC
            self.driver.execute_script("mobile: swipe", {'direction': 'up'})
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//p[contains(text(), "Can I Record Shows?")]'))).is_displayed()  # Record Shows
            app_version = self.driver.find_element(By.XPATH, '//p[@class="F0aslfbXZ_xrEWCBq2tyc"]').text
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
                        "Browser": "Safari",
                        "Device": device,
                        
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
    def test_text_displayed(self):
        try:
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/span/button/div'))).click()  # Click on the Hamburger
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//span[contains(text(), "Settings")]'))).click()  # Click on the Settings button
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//*[@id="react-tabs-0"]')))  # Wait for the page to load
            WebDriverWait(self.driver, 10).until(ec.presence_of_element_located((By.XPATH, '//li[contains(text(), "Legal")]'))).click()  # Click on the Legal button
            WebDriverWait(self.driver, 10).until(ec.presence_of_element_located((By.XPATH, '//h4[contains(text(), "Service Agreement")]')))  # Make sure Service Agreement is present
            WebDriverWait(self.driver, 10).until(ec.presence_of_element_located((By.XPATH, '//h4[contains(text(), "Terms and Conditions")]')))  # Make sure Terms and Conditions is present
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
            self.driver.find_element(By.XPATH, '//a[@href="https://www.dish.com/service-agreements/"]').click()  # Click on the first link
            time.sleep(5)
            self.driver.find_element(By.XPATH, '//h1[contains(text(), "DISH Network Service Agreements")]').is_displayed()  # Make sure the page loads
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
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/span/button/div'))).click()  # Click on the Hamburger
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//span[contains(text(), "Settings")]'))).click()  # Click on the Settings button
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//*[@id="react-tabs-0"]')))  # Wait for the page to load
            WebDriverWait(self.driver, 10).until(ec.presence_of_element_located((By.XPATH, '//li[contains(text(), "Legal")]'))).click()  # Click on the Legal button
            WebDriverWait(self.driver, 10).until(ec.presence_of_element_located((By.XPATH, '//h4[contains(text(), "Service Agreement")]')))  # Make sure Service Agreement is present
            WebDriverWait(self.driver, 10).until(ec.presence_of_element_located((By.XPATH, '//h4[contains(text(), "Terms and Conditions")]')))  # Make sure Terms and Conditions is present
            self.driver.find_element(By.XPATH, '//a[@href="https://www.dish.com/terms-conditions/"]').click()  # Click on the second link
            time.sleep(5)
            self.driver.find_element(By.XPATH, '//h1[contains(text(), "Important Terms and Conditions")]').is_displayed()  # Make sure the page loads
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
class TestServices:
    def test_services_configured(self):
        try:
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/span/button/div'))).click()  # Click on the Hamburger
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//span[contains(text(), "TV Guide")]'))).click()  # Click on the TV Guide button
            WebDriverWait(self.driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//img[@alt="%s"]' % ChannelCount.first_channel)))  # Wait for the Guide to load
            links = []
            channels = self.driver.find_elements(By.XPATH, '(//a[@class="_2eB_OXy4vbP1Kd9moNzO4j"])')
            for i in range(len(channels)):
                links.append(channels[i].get_attribute("href"))
            all_channels = list(dict.fromkeys(links))
            for link in all_channels:
                channel = link.strip().split('/')[5]
                self.driver.get(link)
                self.driver.refresh()
                if WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//button[@class="h2xyENO_W_yt024oi0MrN"]'))).is_enabled():
                    self.driver.find_element(By.XPATH, '//button[@class="h2xyENO_W_yt024oi0MrN"]').click()
                else:
                    pass
                WebDriverWait(self.driver, 30).until_not(ec.visibility_of_element_located((By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')))
                WebDriverWait(self.driver, 30).until(ec.presence_of_element_located((By.XPATH, '//div[@class="bitmovinplayer-poster"]')))
                time.sleep(9)
                self.driver.save_screenshot(self.direct + str(channel) + ".png")
                time.sleep(1)
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
                            
                        },
                        "time": time.time_ns(),
                        "fields": {
                            "timeout_exception": 1,
                        }
                    }
                ]
                client.write_points(body)
                assert False, "timeout error"