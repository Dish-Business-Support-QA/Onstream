import pytest


def pytest_addoption(parser):
    parser.addoption("--onstream_url", action="store", default="https://test.watchdishtv.com/")


@pytest.fixture()
def onstream_url(request):
    return request.config.getoption("--onstream_url")
