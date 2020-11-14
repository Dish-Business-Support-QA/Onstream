import subprocess
from threading import Thread


def pytest_run():
    while True:
        subprocess.run(['pytest', 'OnStream_Chrome.py', '-v', '-s'])


if __name__ == "__main__":
    t1 = Thread(target=pytest_run)
    t1.start()
    t1.join()
