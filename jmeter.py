import subprocess
import pandas as pd

report = open("/Users/dishbusiness/Desktop/jmeter_report.txt", "w")

subprocess.call(['jmeter', '-n', '-t',
                 '/Users/dishbusiness/Desktop/bzm_streaming_sampler.jmx'], stdout=report)

with open("/Users/dishbusiness/Desktop/jmeter_report.txt", "r", encoding='ISO-8859-1') as r, \
        open("/Users/dishbusiness/Desktop/jmeter_report.csv", "a+") as j:
    for line in r:
        if "summary" in line:
            j.write(line)

df = pd.read_csv('/Users/dishbusiness/Desktop/jmeter_report.csv', names=['summary', 'na', 'time1', 'in', 'elapsed_time', 'equal', 'difference', 'avg', 'time2', 'min', 'time3', 'max', 'time4', 'err', 'err_amount', 'percent_err', 'active', 'active_number', 'started', 'started_num', 'finished', 'finished_num'], delim_whitespace=True, error_bad_lines=False)
df.to_csv('/Users/dishbusiness/Desktop/jmeter_report_finished.csv')
