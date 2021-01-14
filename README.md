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

