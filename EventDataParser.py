import json
import pandas as pd
from openpyxl import load_workbook

with open('/Users/dishbusiness/Desktop/OnStreamTestFiles/Duration/Event_Time_Log.json', 'r') as j:
    data = json.load(j)
t = len(data["commands"])

for i in range(0, t):
    p = (data["commands"][i]["endTime"] - data["commands"][i]["startTime"]) / 1000
    t = data["commands"][i]["cmd"]
    print("%s took %.4f seconds" % (t, p),
          file=open('/Users/dishbusiness/Desktop/OnStreamTestFiles/Duration/test.csv', 'a+'))

df = pd.read_csv('/Users/dishbusiness/Desktop/OnStreamTestFiles/Duration/test.csv',
                 names=['Action', 'took', 'time', 'seconds'], delim_whitespace=True, error_bad_lines=False)
df.drop(['took', 'seconds'], axis=1, inplace=True)
mean = df.groupby(['Action']).mean()
dfs = pd.merge(df, mean, on='Action')

file = r'/Users/dishbusiness/Desktop/OnStreamTestFiles/duration.xlsx'
book = load_workbook(file)
writer = pd.ExcelWriter(file, engine='openpyxl')
writer.book = book

dfs.to_excel(writer, sheet_name='test')
writer.save()
writer.close()
