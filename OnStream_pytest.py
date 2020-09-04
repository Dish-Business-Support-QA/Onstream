#! /usr/bin/env monkeyrunner

from __future__ import print_function

import pytest
import os
import psutil
import subprocess
from datetime import datetime

now = datetime.now()

pid = os.getpid()
py = psutil.Process(pid)
MemoryUse = py.memory_info()[0]/2.**30
print('Memory Used:', MemoryUse)

mem = psutil.virtual_memory()
print(mem)

percent = psutil.cpu_percent(interval=1)
print(percent)

subprocess.call(['pytest', '--durations=0', 'OnStream_Chrome.py', '-v', '-s', '-vv'])

print('Memory Used:', MemoryUse)
print(mem)
print(percent)