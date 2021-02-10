import os
import platform
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from threading import Thread
from influxdb import InfluxDBClient

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
    grafana = os.environ['GRAFANA']
except KeyError:
    print('Could not get environment variable "grafana". This is needed for the tests!"')
    raise
try:
    picture_path = os.environ['ONSTREAM_PICTURES']
except KeyError:
    print('Could not get environment variable "test_path". This is needed for the tests!"')
    raise

client = InfluxDBClient(host=grafana, port=8086, database='ONSTREAM')

plat = platform.platform().split('-')
device = str(plat[0] + "-" + plat[1])
version = '1.3.0'
name = os.environ.get('PYTEST_CURRENT_TEST')
direct = os.path.join(picture_path) + "/"


class ChannelCount(object):
    from selenium import webdriver
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
    from selenium.webdriver.chrome.service import Service
    caps = DesiredCapabilities.CHROME
    caps['goog:loggingPrefs'] = {'performance': 'ALL'}
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, desired_capabilities=caps)
    dishtv = "https://davita.watchdishtv.com/"
    driver.get(dishtv)
    WebDriverWait(driver, 30).until(ec.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[1]/div[2]/span/span[2]/a/span'))).click()  # Click on the TV Guide Button
    WebDriverWait(driver, 30).until_not(ec.visibility_of_element_located((By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')))  # Wait for the loading screen to disappear
    WebDriverWait(driver, 30).until(ec.visibility_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/div/div[2]/div/div[2]/div/div/div/div[1]/div[1]')))  # Wait for the TODAY text to appear
    links = []
    channels = driver.find_elements(By.XPATH, '//a[@class="_2GEDK4s6kna2Yfl6_0Q6c_"]')  # Get the Video Player Classes
    for i in range(len(channels)):
        links.append(channels[i].get_attribute("href"))
    all_channels = list(dict.fromkeys(links))
    first_channel = all_channels[0].split('/')[5]
    driver.quit()


class WebDrivers(object):
    def __init__(self):
        self.dishtv = "https://davita.watchdishtv.com/"

    def chrome(self):
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
        from selenium.webdriver.chrome.service import Service
        caps = DesiredCapabilities.CHROME
        test_start = [
            {
                "measurement": "OnStream",
                "tags": {
                    "Software": version,
                    "Test": mc.get_value(),
                    "URL": ChannelCount.dishtv,
                    "Browser": "Chrome",
                },
                "time": time.time_ns(),
                "fields": {
                    "events_title": "test start",
                    "text": "This is the start of test " + mc.get_value() + " on firmware " + version + " tested on " + ChannelCount.dishtv,
                    "tags": "Onstream" + "," + "Chrome" + "," + mc.get_value() + "," + version + "," + ChannelCount.dishtv
                }
            }
        ]
        client.write_points(test_start)
        caps['goog:loggingPrefs'] = {'performance': 'ALL'}
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, desired_capabilities=caps)
        driver.get(self.dishtv)
        try:
            WebDriverWait(driver, 30).until(ec.presence_of_element_located((By.XPATH, '//button[@class="_2YXx31Mkp4UfixOG740yi7 schema_accent_background"]'))).click()
            WebDriverWait(driver, 30).until_not(ec.visibility_of_element_located((By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')))
            WebDriverWait(driver, 30).until(ec.presence_of_element_located((By.XPATH, '//img[@alt="%s"]' % ChannelCount.first_channel)))
            links = []
            channels = driver.find_elements(By.XPATH, '(//a[@class="_2GEDK4s6kna2Yfl6_0Q6c_"])')
            for i in range(len(channels)):
                links.append(channels[i].get_attribute("href"))
            all_channels = list(dict.fromkeys(links))
            for link in all_channels:
                channel = link.strip().split('/')[5]
                driver.get(link)
                driver.refresh()
                try:
                    if WebDriverWait(driver, 30).until(ec.presence_of_element_located((By.XPATH, '//button[@class="TGyzX_NHJqx9WzvYDiQ5g"]'))).is_enabled():
                        driver.find_element(By.XPATH, '//button[@class="TGyzX_NHJqx9WzvYDiQ5g"]').click()
                    else:
                        pass
                except TimeoutException:
                    pass
                WebDriverWait(driver, 30).until_not(ec.visibility_of_element_located((By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')))
                WebDriverWait(driver, 30).until(ec.presence_of_element_located((By.XPATH, '//div[@class="bitmovinplayer-poster"]')))
                time.sleep(5)
                driver.save_screenshot(direct + str(channel) + ".png")
            driver.quit()
            test_end = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": version,
                        "Test": mc.get_value(),
                        "URL": ChannelCount.dishtv,
                        "Browser": "Chrome",
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "events_title": "test end",
                        "text": "This is the end of test " + mc.get_value() + " on firmware " + version + " tested on " + ChannelCount.dishtv,
                        "tags": "Onstream" + "," + "Chrome" + "," + mc.get_value() + "," + version + "," + ChannelCount.dishtv
                    }
                }
            ]
            client.write_points(test_end)
        except NoSuchElementException:
            driver.save_screenshot(direct + name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": version,
                        "Test": mc.get_value(),
                        "Pytest": name,
                        "URL": ChannelCount.dishtv,
                        "Browser": "Chrome",
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
            driver.save_screenshot(direct + name + ".png")
            loading_circle = driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Chrome",
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
                            "Pytest": name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Chrome",
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
                            "Pytest": name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Chrome",
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
                            "Pytest": name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Chrome",
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
                            "Pytest": name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Chrome",
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
                            "Pytest": name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Chrome",
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

    def edge(self):
        from webdriver_manager.microsoft import EdgeChromiumDriverManager
        from msedge.selenium_tools import EdgeOptions
        from selenium.webdriver.edge.service import Service
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
        caps = EdgeOptions()
        caps.use_chromium = True
        service = Service(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(options=caps, service=service)
        driver.get(self.dishtv)
        try:
            WebDriverWait(driver, 30).until(ec.presence_of_element_located((By.XPATH, '//button[@class="_2YXx31Mkp4UfixOG740yi7 schema_accent_background"]'))).click()
            WebDriverWait(driver, 30).until_not(ec.visibility_of_element_located((By.XPATH,
                                                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')))
            WebDriverWait(driver, 30).until(ec.presence_of_element_located((By.XPATH, '//img[@alt="%s"]' % ChannelCount.first_channel)))
            links = []
            channels = driver.find_elements(By.XPATH, '(//a[@class="_2GEDK4s6kna2Yfl6_0Q6c_"])')
            for i in range(len(channels)):
                links.append(channels[i].get_attribute("href"))
            all_channels = list(dict.fromkeys(links))
            for link in all_channels:
                channel = link.strip().split('/')[5]
                driver.get(link)
                driver.refresh()
                try:
                    if WebDriverWait(driver, 30).until(ec.presence_of_element_located((By.XPATH, '//button[@class="TGyzX_NHJqx9WzvYDiQ5g"]'))).is_enabled():
                        driver.find_element(By.XPATH, '//button[@class="TGyzX_NHJqx9WzvYDiQ5g"]').click()
                    else:
                        pass
                except TimeoutException:
                    pass
                WebDriverWait(driver, 30).until_not(ec.visibility_of_element_located((By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')))
                WebDriverWait(driver, 30).until(ec.presence_of_element_located((By.XPATH, '//div[@class="bitmovinplayer-poster"]')))
                time.sleep(5)
                driver.save_screenshot(direct + str(channel) + ".png")
            driver.quit()
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
        except NoSuchElementException:
            driver.save_screenshot(direct + name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": version,
                        "Test": mc.get_value(),
                        "Pytest": name,
                        "URL": ChannelCount.dishtv,
                        "Browser": "Edge",
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
            driver.save_screenshot(direct + name + ".png")
            loading_circle = driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Edge",
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
                            "Pytest": name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Edge",
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
                            "Pytest": name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Edge",
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
                            "Pytest": name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Edge",
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
                            "Pytest": name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Edge",
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
                            "Pytest": name,
                            "URL": ChannelCount.dishtv,
                            "Browser": "Edge",
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
        
    def safari(self):
        test_start = [
            {
                "measurement": "OnStream",
                "tags": {
                    "Software": version,
                    "Test": mc.get_value(),
                    "URL": ChannelCount.dishtv,
                    "Browser": "Safari",
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
        driver = webdriver.Safari(executable_path='/usr/bin/safaridriver')
        driver.get(self.dishtv)
        try:
            WebDriverWait(driver, 30).until(ec.presence_of_element_located((By.XPATH, '//button[@class="_2YXx31Mkp4UfixOG740yi7 schema_accent_background"]'))).click()
            WebDriverWait(driver, 30).until_not(ec.visibility_of_element_located((By.XPATH,
                                                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')))
            WebDriverWait(driver, 30).until(ec.presence_of_element_located((By.XPATH, '//img[@alt="%s"]' % ChannelCount.first_channel)))
            links = []
            channels = driver.find_elements(By.XPATH, '(//a[@class="_2GEDK4s6kna2Yfl6_0Q6c_"])')
            for i in range(len(channels)):
                links.append(channels[i].get_attribute("href"))
            all_channels = list(dict.fromkeys(links))
            for link in all_channels:
                channel = link.strip().split('/')[5]
                driver.get(link)
                driver.refresh()
                try:
                    if WebDriverWait(driver, 30).until(ec.presence_of_element_located((By.XPATH, '//button[@class="TGyzX_NHJqx9WzvYDiQ5g"]'))).is_enabled():
                        driver.find_element(By.XPATH, '//button[@class="TGyzX_NHJqx9WzvYDiQ5g"]').click()
                    else:
                        pass
                except TimeoutException:
                    pass
                WebDriverWait(driver, 30).until_not(ec.visibility_of_element_located((By.XPATH, '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')))
                WebDriverWait(driver, 30).until(ec.presence_of_element_located((By.XPATH, '//div[@class="bitmovinplayer-poster"]')))
                time.sleep(5)
                driver.save_screenshot(direct + str(channel) + ".png")
            driver.quit()
            test_end = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": version,
                        "Test": mc.get_value(),
                        "URL": ChannelCount.dishtv,
                        "Browser": "Safari",
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
        except NoSuchElementException:
            driver.save_screenshot(direct + name + ".png")
            body = [
                {
                    "measurement": "OnStream",
                    "tags": {
                        "Software": version,
                        "Test": mc.get_value(),
                        "Pytest": name,
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
            driver.save_screenshot(direct + name + ".png")
            loading_circle = driver.find_elements(By.XPATH,
                                                       '//div[@class="nvI2gN1AMYiKwYvKEdfIc schema_accent_border-bottom schema_accent_border-right schema_accent_border-left"]')
            no_streaming = driver.find_elements(By.XPATH,
                                                     '//h1[contains(text(), "It appears that you are not able to connect to Streaming Services at this time.")]')
            error_404 = driver.find_elements(By.XPATH, '//h1[contains(text(), "Oops! Error 404")]')
            loading_element = driver.find_elements(By.XPATH, '//span[contains(text(), "Loading...")]')
            went_wrong = driver.find_elements(By.XPATH,
                                                   '//h2[contains(text(), "Something went wrong with the stream.")]')
            if len(loading_circle) > 0:
                body = [
                    {
                        "measurement": "OnStream",
                        "tags": {
                            "Software": version,
                            "Test": mc.get_value(),
                            "Pytest": name,
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
                            "Pytest": name,
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
                            "Pytest": name,
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
                            "Pytest": name,
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
                            "Pytest": name,
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
                            "Pytest": name,
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

    def firefox(self):
        from webdriver_manager.firefox import GeckoDriverManager
        from selenium.webdriver.firefox.service import Service
        service = Service(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service)
        driver.get(self.dishtv)
        driver.quit()

    def opera(self):
        from webdriver_manager.opera import OperaDriverManager
        driver = webdriver.Opera(executable_path=OperaDriverManager().install())
        driver.get(self.dishtv)
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
        self.change = 15

    def get_number(self):
        return self.change


mc = CountRun()
cc = ChannelChange()
wd = WebDrivers()


def pytest_run():
    channels = ChannelCount.all_channels
    results = []
    for name, method in WebDrivers.__dict__.items():
        if callable(method):
            mc.reset()
            while int(len(channels)) < int(cc.get_number()):
                mc.increment()
                mc.save_value()
                results.append(method(wd))
                channels = ChannelCount.all_channels + channels
        channels = ChannelCount.all_channels


if __name__ == "__main__":
    t1 = Thread(target=pytest_run)
    t1.start()
    t1.join()
