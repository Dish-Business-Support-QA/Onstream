import pytest
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver


@pytest.fixture(scope="function")
def chrome_driver_init(request, screenshot_url, pytestconfig):
    chrome_driver = webdriver.Chrome(ChromeDriverManager().install())
    request.cls.driver = chrome_driver
    yield
    if request.node.rep_call.failed and pytestconfig.getoption('--pytest-influxdb'):
        screenshot_link = 'localhost'
        chrome_driver.save_screenshot(screenshot_link)
        screenshot_url(screenshot_link)
    chrome_driver.close()
