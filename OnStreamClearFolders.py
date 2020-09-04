#! /usr/bin/env monkeyrunner
from __future__ import with_statement

import os
import glob

Logs = glob.glob('/Users/dishbusiness/Desktop/OnStreamTestFiles/Logs/*')
Pictures = glob.glob('/Users/dishbusiness/Desktop/OnStreamTestFiles/Pictures/*')
Duration = glob.glob('/Users/dishbusiness/Desktop/OnStreamTestFiles/Duration/*')

for f in Logs:
    os.remove(f)

for f in Pictures:
    os.remove(f)

for f in Duration:
    os.remove(f)