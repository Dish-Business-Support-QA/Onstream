#! /usr/bin/env monkeyrunner
from __future__ import with_statement

import os
import shutil
"""from OnStream_FireTV import version
from OnStream_FireTV import test"""
from OnStream_FireTV_PerformanceTest import version
from OnStream_FireTV_PerformanceTest import test

path = '/Users/dishbusiness/Desktop/OnStreamTestFiles'
Archived = '/Users/dishbusiness/Desktop/OnStreamTestFiles/Archived/' + version + '/' + test

os.mkdir(Archived)

PictureS = '/Users/dishbusiness/Desktop/OnStreamTestFiles/Pictures/'
LogsS = '/Users/dishbusiness/Desktop/OnStreamTestFiles/Logs/'
Duration = '/Users/dishbusiness/Desktop/OnStreamTestFiles/Duration/'

dest = '/Users/dishbusiness/Desktop/OnStreamTestFiles/Archived/' + version + '/' + test

try:
    Picturefiles = os.listdir(PictureS)
    for f in Picturefiles:
        shutil.move(PictureS+f, dest)
except FileNotFoundError:
    print("File Not Found")

try:
    Logfiles = os.listdir(LogsS)
    for f in Logfiles:
        shutil.move(LogsS+f, dest)
except FileNotFoundError:
    print("File Not Found")

try:
    Durationfiles = os.listdir(Duration)
    for f in Durationfiles:
        shutil.move(Duration+f, dest)
except FileNotFoundError:
    print("File Not Found")