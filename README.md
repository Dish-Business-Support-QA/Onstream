# Onstream
This is the folder which contains all of the current test for our OnStream Platform

## Setup
First you will need to create four environment variables which lead to folders which must be created. The environment variables needed to be created are:
*  ONSTREAM_HOME
*  ONSTREAM_TEST
*  ONSTREAM_PICTURES
*  GRAFANA

Two of the variables need to put to folders that must be created on your Desktop. The folders are:
*  OnStreamTestFiles (tied to ONSTREAM_HOME)
*  OnStream_test (tied to ONSTREAM_TEST and ONSTREAM_PICTURES)

An example of how the variables would look on a Ubuntu machine would be:
*  ONSTREAM_HOME="/home/`user`/Desktop/OnStreamTestFiles"
*  ONSTREAM_TEST="/home/`user`/Desktop/OnStream_Test"
*  GRAFANA="localhost" (Or the IP you have set for your Grafana instance)

For Ubuntu I recommend adding the variables to the /etc/environment file, by:
```bash
sudo -H gedit /etc/environment
```
After you will need to reboot your Ubuntu device.

For Mac I recommend adding to the bash_profile file by:
```bash
nano ~/.bash_profile
```
After that you will need to do:
```bash
source ~/.bash_profile
```
Then reboot your Mac

You will also need to create the two above mentioned folders, OnStreamTestFiles and OnStream_Test.

Within OnStream_Test you will need to place the scripts downloaded from this repository.

Within OnStreamTestFiles you will need to create the following subfolders:
*  Archived
*  Duration
*  Logs
*  Pictures

Within this folder you will also need to create a text file named: test_run_num.txt (leave blank).

## Dependicies
You will need to install and have the following running:
*  pytest
*  python3
*  Selenium
*  Influxdb
*  Grafana
*  Appium

## Python Libraries
The following libraries are used within the test:
```python
import os
import platform
import time
import pytest
import pandas
import subprocess
import shutil
import datetime
import webdriver
import Thread
import InfluxDBClient
```

## Grafana Setup
To install Grafana on Ubuntu please use the following commands:
```bash
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
sudo apt update
sudo apt install grafana
```
Once Grafana is installed you will need to start the server, to do so use:
```bash
sudo systemctl start grafana-server
```
To check that it is running use:
```bash
sudo systemctl status grafana-server
```
You should see `Active: active (running)`
To give Grafana the ability to run on startup:
```bash
sudo systemctl enable grafana-server
```
To install Grafana on a Mac:
```bash
brew update
brew install grafana
```
To start the Grafana server:
```bash
brew services start grafana
```

Now you will need to setup a data source locator for InfluxDB. Use the following inputs:
*  Query Language: InfluxQL
*  HTTP: User Configured
*  Auth: User Configured
InfluxDB Details:
*  Database: Onstream
*  User: admin
*  Password: configured
*  HTTP method: blank
*  Min time interval: 10s

You will then need to import the Evolve dashboard. Follow the below steps:
*  Select the +
*  Select Import
*  Select Upload JSON file
*  Use the Onstream-%s.json in the repository
** % this number will change as the Grafana dashboard is modifiyed. Use the one in the Github repo
*  Use the newly created Evolve InfluxDB data source
* Select Import
