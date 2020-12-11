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
import shutil
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
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from pandas.errors import EmptyDataError
from influxdb import InfluxDBClient
from msedge.selenium_tools import EdgeOptions
version = '1.2.27'
caps = EdgeOptions()
caps.use_chromium = True
service = Service(EdgeChromiumDriverManager().install())
driver = webdriver.Edge(options=caps, service=service)


