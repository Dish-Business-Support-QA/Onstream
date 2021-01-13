import json
import time

from pytest_influxdb.data_manager import DataManager


class SuiteResultDTO:
    __run = 'UNDEFINED'
    __project = 'UNDEFINED'
    __version = 'UNDEFINED'
    __passed = None
    __failed = None
    __skipped = None
    __error = None
    __duration_sec = 0
    __disabled = 0
    __retries = 0
    __suite_result_dict = {'tags': {}, 'fields': {}}

    def set_run(self, run):
        if run != '':
            self.__run = str(run)

    def set_project(self, project):
        if project != '':
            self.__project = str(project)

    def set_version(self, version):
        if version != '':
            self.__version = str(version)

    def set_passed(self, passed):
        self.__passed = int(passed)

    def set_failed(self, failed):
        self.__failed = int(failed)

    def set_skipped(self, skipped):
        self.__skipped = int(skipped)

    def set_error(self, error):
        self.__error = int(error)

    def set_duration_sec(self, duration_sec):
        self.__duration_sec = int(duration_sec)

    def set_disabled(self, disabled):
        self.__disabled = int(disabled)

    def set_retries(self, retries):
        self.__retries = int(retries)

    def set_suite_result_dict(self, suite_result_dict):
        SuiteResultDTO.__suite_result_dict = suite_result_dict

    def get_suite_json(self, measurement_name):
        json_body = [
            {
                "measurement": measurement_name,
                "tags": {
                    "run": self.__run,
                    "project": self.__project,
                    "version": self.__version
                },
                "fields": {
                    "pass": self.__passed,
                    "fail": self.__failed,
                    "skip": self.__skipped,
                    "error": self.__error,
                    "disabled": self.__disabled,
                    "duration_sec": self.__duration_sec,
                    "retries": self.__retries
                }
            }
        ]

        # Appending custom values to json_body
        tags_dict = SuiteResultDTO.__suite_result_dict['tags']
        for key in tags_dict:
            suite_tags = json_body[0]['tags']
            suite_tags.update({key: tags_dict[key]})
        fields_dict = SuiteResultDTO.__suite_result_dict['fields']
        for key in fields_dict:
            suite_fields = json_body[0]['fields']
            suite_fields.update({key: fields_dict[key]})

        return json_body

    def set_tag_values(self, tags_dict):
        suite_tags = SuiteResultDTO.__suite_result_dict
        suite_tags['tags'].update(tags_dict)

    def set_field_values(self, fields_dict):
        suite_fields = SuiteResultDTO.__suite_result_dict
        suite_fields['fields'].update(fields_dict)

    def set_suite_custom_values(self, influxdb_values):
        if influxdb_values and influxdb_values != '':
            if isinstance(influxdb_values, str):
                influxdb_values = json.loads(influxdb_values)
            self.set_field_values(influxdb_values['fields']['suite_result'])
            self.set_tag_values(influxdb_values['tags']['suite_result'])

    def get_suite_result_dto(self, terminalreporter, global_values, influxdb_components, db_measurement_name_for_suite):
        # Preparing execution time and suite results from the terminalreporter (where all the data collected)
        execution_time = round(time.time() - terminalreporter._sessionstarttime)
        suite_results_dict = DataManager().get_results_dict(terminalreporter.stats)
        # Setting the values to the suite_result_dto instance
        self.set_passed(suite_results_dict.get('passed'))
        self.set_failed(suite_results_dict.get('failed'))
        self.set_skipped(suite_results_dict.get('skipped'))
        self.set_error(suite_results_dict.get('error'))
        self.set_disabled(suite_results_dict.get('disabled'))
        self.set_duration_sec(execution_time)
        self.set_retries(suite_results_dict.get('reruns'))
        self.set_run(global_values.get("run"))
        self.set_project(global_values.get("project"))
        self.set_version(global_values.get("version"))
        self.set_suite_custom_values(global_values.get("influxdb_values"))

        self.merge_suite_result(global_values.get('merged'), influxdb_components,
                                db_measurement_name_for_suite, global_values.get("run"))

        return self

    def merge_suite_result(self, merged_enabled, influxdb_components, db_measurement_name_for_suite, run_id_value):
        # Merging the existing suite results with the suite_results from db for the same run
        # if 'merged' config value is True
        existing_suite_result = influxdb_components.get_results_by_run(db_measurement_name_for_suite, run_id_value)
        old_suite_list = list(existing_suite_result.get_points(measurement=f'{db_measurement_name_for_suite}'))
        if len(old_suite_list) != 0 and merged_enabled:
            old_suite_total_count = old_suite_list[0]['pass'] + old_suite_list[0]['fail'] + old_suite_list[0][
                'skip']
            old_disabled_tests_count = old_suite_list[0]['disabled']
            self.set_passed(
                old_suite_total_count - self.__failed - self.__skipped)
            self.set_disabled(old_disabled_tests_count)
            influxdb_components.delete_results_by_run(db_measurement_name_for_suite, run_id_value)
