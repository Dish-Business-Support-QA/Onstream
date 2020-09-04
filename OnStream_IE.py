#! /usr/bin/env monkeyrunner

import os
import pytest
import json
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.microsoft import IEDriverManager
from datetime import datetime, timedelta


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
    driver = webdriver.Ie(IEDriverManager().install())
    driver.get("https://watchdishtv.com/")
    driver.maximize_window()
    src = driver.page_source
    request.cls.driver = driver
    request.cls.src = src
    yield
    driver.quit()


@pytest.fixture(scope="class")
def time(request):
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
class TestHomeScreen:
    def test_images_displayed(self):
        WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
            (By.XPATH, '//button[@class="_2YXx31Mkp4UfixOG740yi7 schema_accent_background"]')))
        try:
            self.driver.find_element_by_xpath('//div[@class="_1oUh3apnwdwzBiB_Uw6seb "]').is_displayed()  # banner
            self.driver.find_element_by_xpath('//img[@alt="Dish Logo"]').is_displayed()  # dish
            self.driver.find_element_by_xpath('//img[@alt="Infio Whites"]').is_displayed()  # dish fiber
            self.driver.find_element_by_xpath('//img[@alt="The EnV large"]').is_displayed()  # custom_logo
            self.driver.find_element_by_xpath('//div[@class="Wjmljsl8wM6YcCXO7StJi"]').is_displayed()  # line
            self.driver.find_element_by_xpath('//div[@class="_3h0DRYR6lHf63mKPlX9zwF"]').is_displayed()  # background
            self.driver.find_element_by_xpath \
                ('//span[@class="_3BUdesL_Hri_ikvd5WhZhY _3A8PSs77Wrg10ciWiA2H_B  "]').is_displayed()  # underline
            self.driver.find_element_by_xpath('//div[@class="_2DNEUdY-mRumdYpM8xTEN5"]').is_displayed()  # bottom_image
            self.driver.find_element_by_xpath('//a[@class="_2r6Lq2AYJyfbZABtJvL0D_"]').is_displayed()  # setting
            self.driver.find_element_by_xpath('//hr[@class="K22SRFwz7Os1KInw2zPCQ"]').is_displayed()  # thin_line
            live = self.driver.find_elements_by_xpath('//div[@class="_1acuZqkpaJBNYrvoPzBNq_ _1Ec0IteN1F_Ae9opzh37wr"]')
            for image in live:
                image.is_displayed()  # popular_channels
        except NoSuchElementException as e:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            raise Exception("Element could not be found! Please view the Screenshot!") from e
        except TimeoutException as t:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            raise Exception("The test timed out! Please view the Screenshot!") from t

    def test_buttons_displayed(self):
        try:
            self.driver.find_element_by_xpath('//a[contains(@href,"home")]').is_displayed()  # home
            self.driver.find_element_by_xpath('//a[contains(@href,"epg")]').is_displayed()  # guide
            self.driver.find_element_by_xpath('//a[@class="_2r6Lq2AYJyfbZABtJvL0D_"]').is_displayed()  # setting
            self.driver.find_element_by_xpath\
                ('//button[@class="_2YXx31Mkp4UfixOG740yi7 schema_accent_background"]').is_displayed()  # full guide
            self.driver.find_elements_by_xpath('//div[@class="_1iKpTFW64nBCEODaArwlyd _1encUiSOWTmH2vOVl5BZqy"]')
            self.driver.find_element_by_xpath('//button[@class="_2YXx31Mkp4UfixOG740yi7 null"]').is_displayed()
            # learn_more
            drop_down = self.driver.find_elements_by_xpath\
                ('//a[@class="_1jBpd9Hw7kDuuvGVNTNlax schema_accent_background_hover"]')
            live = self.driver.find_elements_by_xpath('//div[@class="_1iKpTFW64nBCEODaArwlyd _1encUiSOWTmH2vOVl5BZqy"]')
            for button in live:
                button.is_displayed()  # popular_channels
            for button1 in drop_down:
                button1.is_displayed()  # drop_down
        except NoSuchElementException as e:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            raise Exception("Element could not be found! Please view the Screenshot!") from e
        except TimeoutException as t:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            raise Exception("The test timed out! Please view the Screenshot!") from t

    def test_buttons_enabled(self):
        try:
            self.driver.find_element_by_xpath('//a[contains(@href,"home")]').is_enabled()  # home
            self.driver.find_element_by_xpath('//a[contains(@href,"epg")]').is_enabled()  # guide
            self.driver.find_element_by_xpath('//a[@class="_2r6Lq2AYJyfbZABtJvL0D_"]').is_enabled()  # setting
            self.driver.find_element_by_xpath \
                ('//button[@class="_2YXx31Mkp4UfixOG740yi7 schema_accent_background"]').is_enabled()  # full_guide
            self.driver.find_element_by_xpath('//button[@class="_2YXx31Mkp4UfixOG740yi7 null"]').is_enabled()
            # learn_more
            drop_down = self.driver.find_elements_by_xpath \
                ('//a[@class="_1jBpd9Hw7kDuuvGVNTNlax schema_accent_background_hover"]')
            live = self.driver.find_elements_by_xpath\
                ('//a[@class="_2JuEPUlHoO3FulobzI50N5 '
                 '_3RunNS41fFzaeBFbJ1JGwa schema_popularChannelsColors_background"]')
            for button in drop_down:
                button.is_enabled()  # drop_down
            for button1 in live:
                button1.is_enabled()  # live
        except NoSuchElementException as e:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            raise Exception("Element could not be found! Please view the Screenshot!") from e
        except TimeoutException as t:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            raise Exception("The test timed out! Please view the Screenshot!") from t

    def test_text_displayed(self):
        try:
            self.driver.find_element_by_xpath('//span[contains(text(), "Home")]')  # home
            self.driver.find_element_by_xpath('//span[contains(text(), "TV Guide")]')  # guide
            self.driver.find_element_by_xpath('//button[contains(text(), "VIEW FULL TV GUIDE")]')  # full_guide
            self.driver.find_element_by_xpath('//div[contains(text(), "Most Popular Channels")]')  # pop_channels
            self.driver.find_element_by_xpath\
                ('//div[contains(text(), "Want more channels, a DVR, or additional features?")]')  # question
            self.driver.find_element_by_xpath('//div[contains(text(), "Call 866-794-6166")]')  # number
            live = self.driver.find_elements_by_xpath\
                ('//div[@class="_1MhUC88bcyh64jOZVIlotn _3DE_w36fN1va108RdAiaue" and text()="WATCH TV"]')
            for text in live:
                text.is_displayed()  # watch_live
        except NoSuchElementException as e:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            raise Exception("Element could not be found! Please view the Screenshot!") from e
        except TimeoutException as t:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            raise Exception("The test timed out! Please view the Screenshot!") from t

    def test_link_clickable(self):
        try:
            self.driver.find_element_by_xpath('//button[@class="_2YXx31Mkp4UfixOG740yi7 null"]').click()  # learn_more
            self.driver.switch_to.window(self.driver.window_handles[1])  # switch to tab two
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                (By.XPATH, '//img[@alt="DISH Fiber logo"]')))  # wait for dish fiber logo
            self.driver.find_element_by_xpath('//img[@alt="DISH Fiber logo"]').is_displayed()  # dish fiber
            self.driver.switch_to.window(self.driver.window_handles[0])  # switch back to tab one
        except NoSuchElementException as e:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            raise Exception("Element could not be found! Please view the Screenshot!") from e
        except TimeoutException as t:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            raise Exception("The test timed out! Please view the Screenshot!") from t


@pytest.mark.usefixtures("setup", "directory", "time")
class TestGuideScreen:
    def test_images_displayed(self):
        WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
            (By.XPATH, '//button[@class="_2YXx31Mkp4UfixOG740yi7 schema_accent_background"]'))).click()
        WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
            (By.XPATH, '//div[@class="_3s9BHby87YFunQATlfDFIG _13zgmvI0VzaLaUVl9-7siJ"]')))
        try:
            self.driver.find_element_by_xpath('//div[@class="_1oUh3apnwdwzBiB_Uw6seb "]').is_displayed()  # banner
            self.driver.find_element_by_xpath('//img[@alt="Dish Logo"]').is_displayed()  # dish
            self.driver.find_element_by_xpath('//img[@alt="Dish Logo"]').is_displayed()  # custom_logo
            self.driver.find_element_by_xpath('//div[@class="Wjmljsl8wM6YcCXO7StJi"]').is_displayed()  # line
            self.driver.find_element_by_xpath \
                ('//span[@class="_3BUdesL_Hri_ikvd5WhZhY _3A8PSs77Wrg10ciWiA2H_B  "]').is_displayed()  # underline
            self.driver.find_element_by_xpath('//div[@class="_2JbshVQf7cKfzSj6SAqTiq"]').is_displayed()  # channel logos
            self.driver.find_element_by_xpath('//div[@class="_3mtdocLQZjeofa83PD2_vL"]').is_displayed()  # vertical bar
        except NoSuchElementException as e:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            raise Exception("Element could not be found! Please view the Screenshot!") from e
        except TimeoutException as t:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            raise Exception("The test timed out! Please view the Screenshot!") from t

    def test_text_displayed(self):
        try:
            self.driver.find_element_by_xpath\
                ('//div[@class="_1AhFoq9LRVrQE0BrdpGozJ schema_epgTimelineColors_background"]').is_displayed()  # TODAY
            self.driver.find_element_by_xpath\
                ('//div[contains(text(), "%s")]' % self.now).is_displayed()  # Time 1
            self.driver.find_element_by_xpath('//div[contains(text(), "%s")]' % self.now1).is_displayed()  # Time 2
            self.driver.find_element_by_xpath('//div[contains(text(), "%s")]' % self.now2).is_displayed()  # Time 3
            self.driver.find_element_by_xpath('//div[contains(text(), "%s")]' % self.now3).is_displayed()  # Time 4
            self.driver.find_element_by_xpath('//span[contains(text(), "MORE INFO")]').is_displayed()  # More Info
            self.driver.find_element_by_xpath('//span[contains(text(), "WATCH LIVE")]').is_displayed()  # Watch Live
        except NoSuchElementException as e:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            raise Exception("Element could not be found! Please view the Screenshot!") from e
        except TimeoutException as t:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            raise Exception("The test timed out! Please view the Screenshot!") from t

    def test_buttons_displayed(self):
        try:
            self.driver.find_element_by_xpath('//div[@class="_33q8pPVDOZ2wsVJzvR3jdy"]').is_displayed()  # right arrow
            self.driver.find_element_by_xpath('//a[@class="_2GEDK4s6kna2Yfl6_0Q6c_"]').is_displayed()  # play button
            self.driver.find_element_by_xpath('//div[@class="_12Yya3OL4XVr3adIektRU6"]').is_displayed()
            # more info button
            self.driver.find_element_by_xpath('//a[contains(@href,"home")]').is_displayed()  # home button
            self.driver.find_element_by_xpath('//a[@class="_2r6Lq2AYJyfbZABtJvL0D_"]').is_displayed()  # Setting Cog
        except NoSuchElementException as e:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            raise Exception("Element could not be found! Please view the Screenshot!") from e
        except TimeoutException as t:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            raise Exception("The test timed out! Please view the Screenshot!") from t

    def test_buttons_clickable(self):
        try:
            self.driver.find_element_by_xpath('//div[@class="_33q8pPVDOZ2wsVJzvR3jdy"]').is_enabled()  # right arrow
            self.driver.find_element_by_xpath('//a[@class="_2GEDK4s6kna2Yfl6_0Q6c_"]').is_enabled()  # play button
            self.driver.find_element_by_xpath('//div[@class="_12Yya3OL4XVr3adIektRU6"]').is_enabled()
            # more info button
            self.driver.find_element_by_xpath('//a[contains(@href,"home")]').is_enabled()  # home button
            self.driver.find_element_by_xpath('//a[@class="_2r6Lq2AYJyfbZABtJvL0D_"]').is_enabled()  # Setting Cog
        except NoSuchElementException as e:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            raise Exception("Element could not be found! Please view the Screenshot!") from e
        except TimeoutException as t:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            raise Exception("The test timed out! Please view the Screenshot!") from t


@pytest.mark.usefixtures("setup", "directory")
class TestSupportSettingsScreen:
    def test_images_displayed(self):
        try:
            setting = WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                (By.XPATH, '//a[@role="button"]')))  # go to setting button
            ActionChains(self.driver).move_to_element(setting).perform()  # hover mouse over it
            support = WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                (By.XPATH, '//a[@class="_1jBpd9Hw7kDuuvGVNTNlax schema_accent_background_hover"]')))
            # go to support button
            ActionChains(self.driver).move_to_element(support).perform()  # hover mouse over it
            self.driver.find_element_by_xpath\
                ('//a[@class="_1jBpd9Hw7kDuuvGVNTNlax schema_accent_background_hover"]').click()
            # click on support button
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                (By.XPATH, '//div[@class="_1sd7usVW7fcyKBYM7qUANM"]')))  # wait for dish logo
            self.driver.find_element_by_xpath('//div[@class="_1sd7usVW7fcyKBYM7qUANM"]').is_displayed()
            # check that dish logo is displayed
        except NoSuchElementException as e:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            raise Exception("Element could not be found! Please view the Screenshot!") from e
        except TimeoutException as t:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            raise Exception("The test timed out! Please view the Screenshot!") from t

    def test_text_displayed(self):
        try:
            self.driver.find_element_by_xpath\
                ('//h2[contains(text(), "Frequently Asked Questions")]').is_displayed()  # Freq asked questions
            self.driver.find_element_by_xpath\
                ('//p[contains(text(), "What devices are Supported?")]').is_displayed()  # supported devices
            self.driver.find_element_by_xpath\
                ('//p[contains(text(), "How do I get additional channels?")]').is_displayed()  # additional channels
            self.driver.find_element_by_xpath\
                ('//p[contains(text(), "I have access to the streaming '
                 'service but am having an issue, who do I contact?")]').is_displayed()  # who to contact
            self.driver.find_element_by_xpath\
                ('//p[contains(text(), "How do I cast to a TV?")]').is_displayed()  # how to cast
            self.driver.find_element_by_xpath\
                ('//p[contains(text(), "When I leave my property why do I lose access to the service?")]').\
                is_displayed()  # when I leave
            self.driver.find_element_by_xpath\
                ('//p[contains(text(), "Can’t find the answer to what you’re looking for?")]').is_displayed()
            # can't find answers
            self.driver.find_element_by_xpath\
                ('//p[contains(text(), "Please Call Dish Support at: ")]').is_displayed()  # call dish support
            self.driver.find_element_by_xpath\
                ('//p[contains(text(), "1-800-333-DISH")]').is_displayed()  # number to call
        except NoSuchElementException as e:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            raise Exception("Element could not be found! Please view the Screenshot!") from e
        except TimeoutException as t:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            raise Exception("The test timed out! Please view the Screenshot!") from t


@pytest.mark.usefixtures("setup", "directory")
class TestLegalSettingsScreen:
    def test_images_displayed(self):
        try:
            setting = WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                (By.XPATH, '//a[@role="button"]')))  # go to setting button
            ActionChains(self.driver).move_to_element(setting).perform()  # hover mouse over it
            legal = WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                (By.XPATH, '//a[@class="_1jBpd9Hw7kDuuvGVNTNlax schema_accent_background_hover"][2]')))
            # go to legal button
            ActionChains(self.driver).move_to_element(legal).perform()  # hover mouse over it
            self.driver.find_element_by_xpath(
                '//a[@class="_1jBpd9Hw7kDuuvGVNTNlax schema_accent_background_hover"][2]').click()
            # click on legal button
            WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                (By.XPATH, '//div[@class="_2hNvqt9m_HItaYpgkx528X"]')))  # wait for dish logo
            self.driver.find_element_by_xpath('//div[@class="_2hNvqt9m_HItaYpgkx528X"]').is_displayed()
            # check dish logo
        except NoSuchElementException as e:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            raise Exception("Element could not be found! Please view the Screenshot!") from e
        except TimeoutException as t:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            raise Exception("The test timed out! Please view the Screenshot!") from t

    def test_text_displayed(self):
        try:
            self.driver.find_element_by_xpath\
                ('//h2[contains(text(), "Legal")]').is_displayed()  # Legal
            self.driver.find_element_by_xpath\
                ('//h4[contains(text(), "Service Agreements")]').is_displayed()  # Service Agreements
            self.driver.find_element_by_xpath\
                ('//h4[contains(text(), "Terms and conditions")]').is_displayed()  # Terms and conditions
        except NoSuchElementException as e:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            raise Exception("Element could not be found! Please view the Screenshot!") from e
        except TimeoutException as t:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            raise Exception("The test timed out! Please view the Screenshot!") from t

    def test_link1_clickable(self):
        try:
            self.driver.find_element_by_xpath('//a[@href="https://www.dish.com/service-agreements/"]').click()
            # click on link
            self.driver.find_element_by_xpath('//h1[contains(text(), "DISH Network Service Agreements")]').is_displayed()
            # check that Dish network service agreement page populates
        except NoSuchElementException as e:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            raise Exception("Element could not be found! Please view the Screenshot!") from e
        except TimeoutException as t:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            raise Exception("The test timed out! Please view the Screenshot!") from t

    def test_link2_clickable(self):
        try:
            self.driver.get("https://watchdishtv.com/")  # go back to OnStream
            setting = WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                (By.XPATH, '//a[@role="button"]')))  # go to setting button
            ActionChains(self.driver).move_to_element(setting).perform()  # hover mouse over it
            legal = WebDriverWait(self.driver, 30).until(ec.presence_of_element_located(
                (By.XPATH, '//a[@class="_1jBpd9Hw7kDuuvGVNTNlax schema_accent_background_hover"][2]')))
            # go to legal button
            ActionChains(self.driver).move_to_element(legal).perform()  # hover mouse over it
            self.driver.find_element_by_xpath(
                '//a[@class="_1jBpd9Hw7kDuuvGVNTNlax schema_accent_background_hover"][2]').click()
            # click on legal button
            self.driver.find_element_by_xpath('//a[@href="https://www.dish.com/terms-conditions/"]').click()
            # click on link
            self.driver.find_element_by_xpath('//h1[contains(text(), "Important Terms and Conditions")]').is_displayed()
            # check that Important terms and conditions page populates
        except NoSuchElementException as e:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            raise Exception("Element could not be found! Please view the Screenshot!") from e
        except TimeoutException as t:
            self.driver.save_screenshot(self.direct + self.name + ".png")
            raise Exception("The test timed out! Please view the Screenshot!") from t