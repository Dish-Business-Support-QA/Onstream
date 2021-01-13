import json

from pytest_influxdb.test_result_dto import TestResultDTO


class DataManager:
    def get_test_result_dto(self, test_name, session_dict):
        """ :return: 'test_result_dto' instance """
        test_result_dto_dict = session_dict.get('test_result_dto_session_dict')
        test_result_dto_dict.update({test_name: TestResultDTO()})
        test_result_dto: TestResultDTO = test_result_dto_dict.get(test_name)
        test_result_dto.set_test(test_name)
        return test_result_dto

    def get_report(self, request):
        """ :return: Valid report for current stage """
        try:
            report_outcome = request.node.rep_call
        except AttributeError:
            report_outcome = request.node.rep_setup
        return report_outcome

    def get_test_influxdb_components(self, influxdb, session_dict):
        """ Checking if there's an existing db instance, if not creating one
            :return: db instance """
        influxdb_components = session_dict.get('influxdb')
        if not influxdb_components:
            session_dict.update({'influxdb': influxdb})
            influxdb_components = session_dict.get('influxdb')
        return influxdb_components

    def save_db_data_in_properties(self, request, db_host, db_port, db_user, db_password, db_name,
                                   influxdb_values, run, project, version, merged):
        # Saving the data in user_properties
        if not isinstance(influxdb_values, dict):
            influxdb_values = influxdb_values.replace("'", '"')
        custom_values = self.merge_custom_fields(request.node.user_properties, influxdb_values)
        if custom_values != "":
            influxdb_values = custom_values
        request.node.user_properties = ({"influxdb_creds": dict(influxdb_host=db_host, influxdb_port=db_port,
                                                                influxdb_user=db_user,
                                                                influxdb_password=db_password,
                                                                influxdb_name=db_name),
                                         "test_values": dict(influxdb_values=influxdb_values,
                                                             run=run, project=project, version=version,
                                                             merged=merged)},)

    def merge_custom_fields(self, user_properties_fields, influxdb_values):
        # Merging 'influxdb_values' variable and the values in the user_properties
        for var in user_properties_fields:
            if isinstance(var, dict) and len(user_properties_fields[0]) == 1:
                if isinstance(influxdb_values, str) and influxdb_values != '':
                    influxdb_values = json.loads(influxdb_values)
                    influxdb_values['fields']['test_result'].update(var)
                elif isinstance(influxdb_values, dict):
                    influxdb_values['fields']['test_result'].update(var)
                else:
                    influxdb_values = {
                        "fields": {
                            "test_result": var,
                            "suite_result": {
                            }
                        },
                        "tags": {
                            "test_result": {
                            },
                            "suite_result": {
                            }
                        }
                    }
        return influxdb_values

    def get_test_influxdb_credentials(self, terminalreporter):
        """ :return: Influxdb valid credentials from the test node """
        influxdb_creds_dict = dict()
        for test_obj in terminalreporter.stats.get(''):
            if test_obj.when == 'teardown' and ('skip' not in test_obj.keywords):
                user_influxdb_creds_dict = test_obj.user_properties[0].get('influxdb_creds')
                influxdb_creds_dict.update(dict(influxdb_test_host=user_influxdb_creds_dict['influxdb_host'],
                                                influxdb_test_port=user_influxdb_creds_dict['influxdb_port'],
                                                influxdb_test_user=user_influxdb_creds_dict['influxdb_user'],
                                                influxdb_test_password=user_influxdb_creds_dict['influxdb_password'],
                                                influxdb_test_name=user_influxdb_creds_dict['influxdb_name']
                                                ))
                break
        return influxdb_creds_dict

    def get_test_values(self, terminalreporter):
        """ :return: Config values from the test node without db info """
        test_values_dict = dict()
        for test_obj in terminalreporter.stats.get(''):
            if test_obj.when == 'teardown' and ('skip' not in test_obj.keywords):
                user_values_dict = test_obj.user_properties[0].get('test_values')
                test_values_dict.update(dict(influxdb_test_values=user_values_dict['influxdb_values'],
                                             influxdb_run_value=user_values_dict['run'],
                                             influxdb_project_value=user_values_dict['project'],
                                             influxdb_version_value=user_values_dict['version'],
                                             merged=user_values_dict['merged']
                                             ))
                break
        return test_values_dict

    def get_valid_influxdb_values(self, terminalreporter):
        """ :return: Config values from the test with db info """
        influxdb_creds_dict = self.get_test_influxdb_credentials(terminalreporter)
        test_values_dict = self.get_test_values(terminalreporter)

        return dict(db_host=influxdb_creds_dict.get("influxdb_test_host"),
                    db_port=influxdb_creds_dict.get("influxdb_test_port"),
                    db_user=influxdb_creds_dict.get("influxdb_test_user"),
                    db_password=influxdb_creds_dict.get("influxdb_test_password"),
                    db_name=influxdb_creds_dict.get("influxdb_test_name"),
                    influxdb_values=test_values_dict.get("influxdb_test_values"),
                    run=test_values_dict.get("influxdb_run_value"),
                    project=test_values_dict.get("influxdb_project_value"),
                    version=test_values_dict.get('influxdb_version_value'),
                    merged=test_values_dict.get('merged'))

    def get_results_dict(self, collected_test_results):
        """ :return: Dict() with the total executed test results """
        collected_tests = {'passed': collected_test_results.get('passed'),
                           'skipped': collected_test_results.get('skipped'),
                           'error': collected_test_results.get('error'),
                           'failed': collected_test_results.get('failed'),
                           'disabled': collected_test_results.get('xfailed'),
                           'reruns': collected_test_results.get('rerun')}

        for test_type, tests in collected_tests.items():
            if tests is not None:
                collected_tests[test_type] = len(tests)
            else:
                collected_tests[test_type] = 0

        return dict(passed=collected_tests['passed'], skipped=collected_tests['skipped'],
                    failed=collected_tests['failed'], error=collected_tests['error'],
                    disabled=collected_tests['disabled'] + collected_tests['skipped'], reruns=collected_tests['reruns'])

    def send_data_to_db(self, test_result_dto, influxdb, db_measurement_name_for_test, session_dict):
        # Sending the test results to influxdb
        test_json = test_result_dto.get_test_json(db_measurement_name_for_test)
        self.get_test_influxdb_components(influxdb, session_dict).write_points(test_json)

    def send_suite_data_to_db(self, suite_json, influxdb_components):
        # Sending the test results to influxdb
        influxdb_components.write_points(suite_json)
