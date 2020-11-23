import os
import csv
import pytest
import json
import time
import glob
import re
import pandas as pd
import numpy as np
import linecache
import time
import subprocess
from collections import Counter
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Thread
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException, JavascriptException, StaleElementReferenceException, ElementNotInteractableException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.opera import OperaDriverManager
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import pychromecast
from pandas.errors import EmptyDataError

try:
    base_path = os.environ['ONSTREAM_HOME']
except KeyError:
    print('Could not get environment variable "base_path". This is needed for the tests!"')
    raise


class ChannelChange:
    def __init__(self):
        print("Please enter how many channel changes you wish to occur!")
        self.change = input()
        self.num = self.change

    def get_number(self):
        return self.change

    def number(self):
        return self.num


cc = ChannelChange()

cc.get_number()

print(cc.number())
