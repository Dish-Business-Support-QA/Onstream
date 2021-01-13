import pytest

from pytest_influxdb.data_manager import DataManager
from pytest_influxdb.influxdb_components import Influxdb_Components
from pytest_influxdb.suite_result_dto import SuiteResultDTO

data_manager = DataManager()
test_result_dto_session_dict = dict()
session_dict = {'test_result_dto_session_dict': test_result_dto_session_dict}
db_measurement_name_for_test = 'test_result'
db_measurement_name_for_suite = 'suite_result'


@pytest.mark.tryfirst
def pytest_runtest_makereport(item, call, __multicall__):
    # Preparing the record for test results
    if item.config.option.pytest_influxdb:
        report = __multicall__.execute()
        setattr(item, "rep_" + report.when, report)
        return report


@pytest.fixture(scope='function', autouse=True)
def test_result(request, pytestconfig, get_influxdb, run, influxdb_project, version, influxdb_values, db_host, db_port, db_name,
                db_user, db_password, merged):
    # Getting the test name of the current node for generating the test result data
    test_name = request.node.nodeid
    test_result_dto = data_manager.get_test_result_dto(test_name, session_dict)
    # Sending the data to db after test execution when the plugin is activated
    if pytestconfig.getoption('--pytest-influxdb'):
        def send_test_data_to_db():
            # Generating test data
            data_manager.save_db_data_in_properties(request=request, db_host=db_host, db_port=db_port, db_user=db_user,
                                                    db_password=db_password, db_name=db_name,
                                                    influxdb_values=influxdb_values, run=run, project=influxdb_project,
                                                    version=version, merged=merged)

            test_result_dto.set_test_result_data(influxdb_project, version, run, data_manager.get_report(request), merged,
                                                 request)
            try:
                data_manager.send_data_to_db(test_result_dto, get_influxdb, db_measurement_name_for_test, session_dict)
            except:
                print("InfluxDB Connection problem raised when sending test data to db.")

        request.addfinalizer(send_test_data_to_db)


def pytest_exception_interact(node, call, report):
    # Generating exception info when test is failed
    if report.failed:
        test_name = node.nodeid
        test_result_dto = session_dict.get('test_result_dto_session_dict').get(test_name)
        if test_result_dto:
            stack_trace = node.repr_failure(call.excinfo)
            stack_trace = str(stack_trace).replace('"', "'")
            test_result_dto.set_exception(stack_trace)


def pytest_configure(config):
    # Passing ini configs to 'config' fixture
    config.getini("influxdb_run_id")
    config.getini("influxdb_project")
    config.getini("influxdb_version")
    config.getini("influxdb_host")
    config.getini("influxdb_port")
    config.getini("influxdb_user")
    config.getini("influxdb_password")
    config.getini("influxdb_name")
    config.getini("influxdb_project")
    config.getini("influxdb_values")


def pytest_addoption(parser):
    # Declaring config variables from the CLI variables and variables in .ini file
    group = parser.getgroup('pytest-influxdb')
    group.addoption("--pytest-influxdb", action="store_true",
                    help="pytest-influxdb: enable influxdb data collection")
    parser.addoption(
        "--influxdb_run_id", action="store", default=None, help="my option: run_id"
    )
    parser.addoption(
        "--influxdb_host", action="store", default=None, help="my option: db_host"
    )
    parser.addoption(
        "--influxdb_port", action="store", default=None, help="my option: db_port"
    )
    parser.addoption(
        "--influxdb_user", action="store", default=None, help="my option: db_username"
    )
    parser.addoption(
        "--influxdb_password", action="store", default=None, help="my option: db_password"
    )
    parser.addoption(
        "--influxdb_name", action="store", default=None, help="my option: db_name"
    )
    parser.addoption(
        "--influxdb_project", action="store", default=None, help="my option: project name"
    )
    parser.addoption(
        "--influxdb_version", action="store", default=None, help="my option: version"
    )
    parser.addoption(
        "--influxdb_values", action="store", default=None, help="my option: values"
    )
    parser.addoption(
        "--influxdb_merged", action="store_true", default=None, help="my option: merged"
    )
    parser.addini(
        'influxdb_run_id',
        help='my option: run_id')
    parser.addini(
        'influxdb_project',
        help='my option: project')
    parser.addini(
        'influxdb_version',
        help='my option: version')
    parser.addini(
        'influxdb_host',
        help='my option: db_host')
    parser.addini(
        'influxdb_port',
        help='my option: db_port')
    parser.addini(
        'influxdb_name',
        help='my option: db_name')
    parser.addini(
        'influxdb_user',
        help='my option: db_user')
    parser.addini(
        'influxdb_password',
        help='my option: db_password')
    parser.addini(
        'influxdb_values',
        help='my option: db_values')


@pytest.fixture
def run(request, pytestconfig):
    """ :return: 'run_id' value """
    run_id = request.config.getoption("--influxdb_run_id")
    if not run_id:
        run_id = pytestconfig.getini('influxdb_run_id')
    return run_id


@pytest.fixture
def db_host(request, pytestconfig):
    """ :return: 'db_host' value """
    db_host = request.config.getoption("--influxdb_host")
    if not db_host:
        db_host = pytestconfig.getini("influxdb_host")
    return db_host


@pytest.fixture
def db_port(request, pytestconfig):
    """ :return: 'db_port' value """
    db_port = request.config.getoption("--influxdb_port")
    if not db_port:
        db_port = pytestconfig.getini("influxdb_port")
    if not db_port:
        db_port = 8086
    return db_port


@pytest.fixture
def db_user(request, pytestconfig):
    """ :return: 'db_user' value """
    db_user = request.config.getoption("--influxdb_user")
    if not db_user:
        db_user = pytestconfig.getini("influxdb_user")
    return db_user


@pytest.fixture
def db_password(request, pytestconfig):
    """ :return: 'db_password' value """
    db_password = request.config.getoption("--influxdb_password")
    if not db_password:
        db_password = pytestconfig.getini("influxdb_password")
    return db_password


@pytest.fixture
def db_name(request, pytestconfig):
    """ :return: 'db_name' value """
    db_name = request.config.getoption("--influxdb_name")
    if not db_name:
        db_name = pytestconfig.getini("influxdb_name")
    return db_name


@pytest.fixture
def influxdb_project(request, pytestconfig):
    """ :return: 'project' value """
    project_name = request.config.getoption("--influxdb_project")
    if not project_name:
        project_name = pytestconfig.getini('influxdb_project')
    return project_name


@pytest.fixture
def version(request, pytestconfig):
    """ :return: 'version' value """
    version = request.config.getoption("--influxdb_version")
    if not version:
        version = pytestconfig.getini('influxdb_version')
    return version


@pytest.fixture
def influxdb_values(request, pytestconfig):
    """ :return: 'influxdb_values' value """
    values = request.config.getoption("--influxdb_values")
    if not values:
        values = pytestconfig.getini("influxdb_values")
    return values


@pytest.fixture()
def merged(request):
    """ :return: 'merged' boolean value """
    return request.config.getoption("--influxdb_merged")


@pytest.fixture()
def get_influxdb(pytestconfig, db_host, db_port, db_name, db_user, db_password):
    """ :return: New Instance of Influxdb_Components """
    if pytestconfig.getoption('--pytest-influxdb'):
        influxdb_components = Influxdb_Components(db_host, db_port, db_user, db_password, db_name)
        return influxdb_components


@pytest.fixture()
def screenshot_url(request, pytestconfig):
    # Fixture for generating a screenshot from conftest
    if pytestconfig.getoption('--pytest-influxdb'):
        current_test = request.node.nodeid

        def _foo(*args, **kwargs):
            test_result_dto = session_dict.get('test_result_dto_session_dict').get(current_test)
            if pytestconfig.getoption('--pytest-influxdb'):
                test_result_dto.set_screenshot(args[1])
            return (args, kwargs)

        return _foo


@pytest.hookimpl(hookwrapper=True)
def pytest_terminal_summary(config, terminalreporter):
    # Preparing summarize report for suite_results
    yield
    all_tests_report = terminalreporter.stats
    if config.getoption('--pytest-influxdb') and len(all_tests_report) > 0 and not are_tests_skipped(all_tests_report):
        global_values = data_manager.get_valid_influxdb_values(terminalreporter)
        influxdb_components = Influxdb_Components(global_values.get("db_host"), global_values.get("db_port"),
                                                  global_values.get("db_user"), global_values.get("db_password"),
                                                  global_values.get("db_name"))

        suite_result_dto = SuiteResultDTO().get_suite_result_dto(terminalreporter, global_values, influxdb_components,
                                                                 db_measurement_name_for_suite)
        if global_values.get("run") != '' and global_values.get("run") != 'UNDEFINED':
            try:
                suite_json = suite_result_dto.get_suite_json(db_measurement_name_for_suite)
                data_manager.send_suite_data_to_db(suite_json, influxdb_components)
            except:
                print("Influxdb connection problem raised when sending suite data to db.")


def are_tests_skipped(terminalreporter_values):
    are_all_tests_skipped = False
    all_tests = terminalreporter_values.get('')
    if 'skipped' in terminalreporter_values:
        are_all_tests_skipped = len(all_tests) == len(terminalreporter_values['skipped'])
    return are_all_tests_skipped