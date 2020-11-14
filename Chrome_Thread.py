import os
import subprocess
from threading import Thread

try:
    test_path = os.environ['ONSTREAM_TEST']
except KeyError:
    print('Could not get environment variable "test_path". This is needed for the tests!"')
    raise


def pytest_run():
    while True:
        subprocess.run(['pytest', os.path.join(test_path, 'OnStream_Chrome.py'), '-v', '-s'])


if __name__ == "__main__":
    t1 = Thread(target=pytest_run)
    t1.start()
    t1.join()
