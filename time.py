from datetime import datetime, timedelta

t1 = datetime.now() + timedelta(hours=1)
t2 = datetime.now() + timedelta(hours=2)
t3 = datetime.now() + timedelta(hours=3)

print(datetime.now().strftime('%-H:%M'))

if datetime.now().strftime('%M') < str(30):
    m = str("{0:0>2}".format(0))
elif datetime.now().strftime('%M') >= str(30):
    m = str(30)
now = datetime.now().strftime('%-I:' + m)
now1 = t1.strftime('%-I:' + m)
now2 = t2.strftime('%-I:' + m)
now3 = t3.strftime('%-I:' + m)

print(now)

if ":" + str(30) in now:
    print("yes")
else:
    print("no")