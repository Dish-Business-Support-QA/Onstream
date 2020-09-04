#! /usr/bin/env monkeyrunner
from __future__ import with_statement
from datetime import datetime

import os


log = '/Users/dishbusiness/Desktop/OnStreamTestFiles/Logs/'
pic = '/Users/dishbusiness/Desktop/OnStreamTestFiles/Pictures/'
dur = '/Users/dishbusiness/Desktop/OnStreamTestFiles/Duration/'
pic_list = [os.path.join(pic, x) for x in os.listdir(pic)]
log_list = [os.path.join(log, x) for x in os.listdir(log)]
dur_list = [os.path.join(dur, x) for x in os.listdir(dur)]

for file in pic_list:
    filename, file_extension = os.path.splitext(file)
    date = datetime.fromtimestamp(os.path.getctime(file)).strftime('%Y-%m-%d_%H:%M:%S')
    os.rename(file, os.path.join(pic, filename + date + file_extension))

for file in log_list:
    filename, file_extension = os.path.splitext(file)
    date = datetime.fromtimestamp(os.path.getctime(file)).strftime('%Y-%m-%d_%H:%M:%S')
    os.rename(file, os.path.join(log, filename + date + file_extension))

for file in dur_list:
    filename, file_extension = os.path.splitext(file)
    date = datetime.fromtimestamp(os.path.getctime(file)).strftime('%Y-%m-%d_%H:%M:%S')
    os.rename(file, os.path.join(dur, filename + date + file_extension))