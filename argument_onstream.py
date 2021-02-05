import argparse

parser = argparse.ArgumentParser(description='Setup for Automated OnStream Test')
parser.add_argument("--onstream_url", dest="onstream_url", action="store", default="https://test.watchdishtv.com/", help="The URL for the OnStream instance you wish to test")
parser.add_argument("--smartbox_ip", dest="smartbox_ip", action="store", default="https://10.11.46.143", help="The IP of the SMARTBOX which has the channel lineup for the Onstream instance you are testing with")
parser.add_argument("--onstream_version", dest="onstream_version", action="store", default="1.2.32", help="The OnStream version you will be testing")
parser.add_argument("--channel_loop", dest="channel_loop", action="store", default="40", help="The number of channels you wish to flip through in OnStream")
parser.add_argument("--grafana_ip", dest="grafana_ip", action="store", default="localhost", help="The IP of the Grafana instance")
parser.add_argument("--grafana_port", dest="grafana_port", action="store", default="8086", help="The IP of the Grafana instance")
parser.add_argument("--custom_logo", dest="custom_logo", action="store", default="DaVita Logo", help="The Custom Logo which appears in the middle of the main page for OnStream")

args, unknown = parser.parse_known_args()
