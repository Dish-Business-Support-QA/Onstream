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
from selenium.common.exceptions import NoSuchElementException, TimeoutException, JavascriptException
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

csv_lines = {}  # Global dict to store line of csv information gathered from x time
r_nano = ""  # Global variable to use for nano-second written to current RAM file


class Start(object):  # Class to setup the test run environment
    log = open('/Users/dishbusiness/Desktop/EvolveTestFiles/Logs/log.txt', 'a+', encoding='ISO-8859-1')
    # File to store the logcat
    r = open('/Users/dishbusiness/Desktop/EvolveTestFiles/Logs/InfluxdbEvolve.csv', "a+", newline='')
    # CSV file which houses all the data to be used in Grafana
    fieldnames = ['measurement_name', 'Software', 'RAM', 'CPU', 'error_count', 'has-died_count', 'lmk_count',
                  'low_on_memory_count', 'time']  # Column names for CSV file
    writer = csv.DictWriter(r, fieldnames=fieldnames)  # Create CSV file with Column names
    writer.writeheader()  # Write the Column names to file
    r.close()  # close the CSV file
    subprocess.call(['adb', 'logcat', '-c'])  # Clear logcat of old data
    subprocess.call(['adb', 'logcat', '-G', '16Mb'])  # Change size of logcat writing to 16MB
    subprocess.Popen(['adb', 'logcat'], stdout=log)  # Open instance and start writing logcat to log.txt
    subprocess.Popen(['telegraf', '--config', '/Users/dishbusiness/Desktop/EvolveTestFiles/EVOLVE.conf'])
    # Open instance of telegraf to export data from CSV file to InfluxDB


def run():  # Thread to make sure CSV file does not have a blank time cell
    while True:
        try:
            df = pd.read_csv('/Users/dishbusiness/Desktop/EvolveTestFiles/Logs/InfluxdbEvolve.csv', header=0)
            # Read csv file to memory
            data = len(df.index)  # Count rows
            df1 = df[df.time != int(0)]  # Erase rows with no data in Column time
            data1 = len(df1.index)  # Count rows from new dataframe
            if data > data1:  # If dataframe data has more rows than dataframe data1
                df1.to_csv('/Users/dishbusiness/Desktop/EvolveTestFiles/Logs/InfluxdbEvolve.csv', index=False)
                # Write dataframe df1 as new CSV file
                time.sleep(1)
                continue
            else:  # If dataframe data has less rows than dataframe data1 do nothing
                time.sleep(1)
                continue
        except EmptyDataError:
            pass


def run2():  # Thread to extract new data from RAM text files into CSV file with timestamp
    class RAMHandler(FileSystemEventHandler):  # Watchdog folder monitor Class
        def on_created(self, event):  # When file is created in monitored folder
            global csv_lines, r_nano  # Call global variables set outside of Class
            new_ram = str(event.src_path)  # Extract filepath from new file in monitored folder
            r_base = os.path.basename(new_ram)  # Strip filepath too base file name
            r_nano = r_base.strip('RAM_ .txt')  # Strip nanosecond time from file name
            with open(new_ram, "r", encoding='ISO-8859-1') as r_in:  # Open new RAM file
                for line in r_in:
                    if 'MemAvailable:' in line:  # Find line with MemAvailable
                        csv_lines = {"measurement_name": "Evolve", "Software": "1.06e", "RAM": line.strip(
                            "MemAvailable: \n kB"), "time": r_nano}
                        #  Write information to global dict (csv_lines) where line found is stripped to just the number
                        return csv_lines, r_nano
    r_observer = Observer()
    r_event_handler = RAMHandler()
    r_observer.schedule(r_event_handler, path='/Users/dishbusiness/Desktop/EvolveTestFiles/RAM_db')  # Folder to monitor
    r_observer.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        r_observer.stop()

    r_observer.join()


def run3():  # Thread to extract new data from CPU text files into CSV file
    class CPUHandler(FileSystemEventHandler):  # Watchdog folder monitor Class
        def on_created(self, event):  # When file is created in monitored folder
            new_cpu = str(event.src_path)  # Extract filepath from new file in monitored folder
            time.sleep(1)
            with open(new_cpu, 'r', encoding='utf-8', errors='ignore') as c_in:  # Open new CPU file
                if "RAM" in csv_lines:  # Make sure RAM was written to csv_lines dict
                    for q, line in enumerate(c_in):  # read file as numbered lines
                        if q == 3:  # Go to line 4
                            idle = line.split("%sys ")[1].split("%")[0]  # Extract just the idle number
                            c = {"CPU": int(idle)}  # write CPU Idle variable c
                            csv_lines.update(c)  # updated csv_lines dict with CPU Idle
                            break
                else:
                    pass
    c_observer = Observer()
    c_event_handler = CPUHandler()
    c_observer.schedule(c_event_handler, path='/Users/dishbusiness/Desktop/EvolveTestFiles/CPU_db')  # Folder to monitor
    c_observer.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        c_observer.stop()

    c_observer.join()


def run4():  # Thread to extract data from log file
    while True:
        if "CPU" in csv_lines:  # Make sure CPU was written csv_lines dict
            wanted = ['died', 'error', 'lowmemorykiller', 'Low on memory']  # strings to look for in log file
            cnt = Counter()
            words = re.findall('\w+', open('/Users/dishbusiness/Desktop/EvolveTestFiles/Logs/log.txt',
                                           encoding='ISO-8859-1').read().lower())  # find all instances of strings
            for word in words:
                if word in wanted:
                    cnt[word] += 1  # create a count of each individual string in wanted found in words
            error = cnt['error']
            has_died = cnt['died']
            lmk = cnt['lowmemorykiller']
            low_on_memory = cnt['low on memory']
            # Take the count of the individual strings and write to csv file for storage
            with open('/Users/dishbusiness/Desktop/EvolveTestFiles/logs/num.csv', 'w', newline='') as out:
                fieldnames = ['error_count', 'has-died_count', 'lmk_count', 'low_on_memory_count']
                writer = csv.DictWriter(out, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow({'error_count': str(error), 'has-died_count': str(has_died), 'lmk_count': str(lmk),
                                 'low_on_memory_count': str(low_on_memory)})
            time.sleep(10)
            with open('/Users/dishbusiness/Desktop/EvolveTestFiles/Logs/num.csv', 'r', newline='') as n_out:
                reader = csv.DictReader(n_out, delimiter=',')  # Read the CSV file from above that has the stored values
                wanted = ['died', 'error', 'lowmemorykiller', 'Low on memory']  # strings to look for in log file
                n_cnt = Counter()
                n_words = re.findall('\w+', open('/Users/dishbusiness/Desktop/EvolveTestFiles/Logs/log.txt',
                                                 encoding='ISO-8859-1').read().lower())  # find all instances of strings
                for n_word in n_words:
                    if n_word in wanted:
                        n_cnt[n_word] += 1  # create a count of each individual string in wanted found in words
                n_error = n_cnt['error']
                n_has_died = n_cnt['has died']
                n_lmk = n_cnt['lowmemorykiller']
                n_low_on_memory = n_cnt['low on memory']
                for row in reader:
                    # Subtract the first count from the second count to get the number of instances over the last 10 sec
                    final_error_count = int(n_error) - int(row['error_count'])
                    final_has_died_count = int(n_has_died) - int(row['has-died_count'])
                    final_lmk_count = int(n_lmk) - int(row['lmk_count'])
                    final_low_on_memory_count = int(n_low_on_memory) - int(row['low_on_memory_count'])
                    e = {"error_count": final_error_count, "has-died_count": final_has_died_count, "lmk_count":
                        final_lmk_count, "low_on_memory_count": final_low_on_memory_count}  # write CPU Idle variable e
                    csv_lines.update(e)  # updated csv_lines dict with counts from log file
        else:
            pass


def run5():  # Thread to write the csv dict for a given nanosecond to the Master CSV file
    while True:
        with open('/Users/dishbusiness/Desktop/EvolveTestFiles/Logs/InfluxdbEvolve.csv', "a+", newline='') as r_out:
            if r_nano not in r_out:  # Make sure duplicate times are not written to file
                if 'low_on_memory_count' in csv_lines:  # Make sure low_on_memory_count is written to csv_lines
                    if 'CPU' in csv_lines:  # Make sure CPU is written to csv_lines
                        n_r_writer = csv.DictWriter(r_out, fieldnames=Start.fieldnames)
                        n_r_writer.writerow(csv_lines)
                        time.sleep(10)
            else:
                print("duplicate")
                break


def run6():  # Thread to capture data from the Evolve every 10 seconds
    while True:
        t = time.time_ns()  # Create a variable for the current nano second
        m = str(1)  # Variable for top command, calls Top one time
        cpu = open("/Users/dishbusiness/Desktop/EvolveTestFiles/CPU_db/CPU_" + str(t) + ".txt", "w")
        # CPU top file with x nanosecond
        ram = open("/Users/dishbusiness/Desktop/EvolveTestFiles/RAM_db/RAM_" + str(t) + ".txt", "w")
        # Meminfo file with x nanosecond
        subprocess.call(['adb', 'shell', 'cat /proc/meminfo'], stdout=ram)  # Capture meminfo from Evolve
        subprocess.call(['adb', 'shell', 'top', '-n', m], stdout=cpu)  # Capture CPU Top from Evolve
        time.sleep(10)


def run7():
    subprocess.call(['pytest', 'Evolve_Grafana.py', '-v', '-s'])
    os._exit(1)


if __name__ == "__main__":
    t1 = Thread(target=run)
    t2 = Thread(target=run2)
    t3 = Thread(target=run3)
    t4 = Thread(target=run4)
    t5 = Thread(target=run5)
    t6 = Thread(target=run6)
    t7 = Thread(target=run7)
    t1.setDaemon(True)
    t5.setDaemon(True)
    t6.setDaemon(True)
    t7.setDaemon(True)
    t1.start()
    t2.start()
    t3.start()
    t4.start()
    t5.start()
    t6.start()
    t7.start()
    t2.join()
    t3.join()
    t4.join()
    while True:
        pass
