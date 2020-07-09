import sys, os, time
import sqlite3
import uuid
import run_parameters_parser as yaml_parser
import database_writer
import collections
import ujson
import json
from collections import defaultdict
## We can get rows back from SQL as a Row object
## This allows us to compare the yaml files and the DB entries more readily.


### Going to try and recreate the YAML python dictionary from DB, then we
### can simply compare dictionaries when they are in the same form.

class DatabaseReader():

    def __init__(self, *args, **kwargs):
        start = time.time()
        self.args = args
        self.kwargs = kwargs
        self.sql_connection = sqlite3.connect('SimulationDatabase.db')
        self.sql_cursor = self.sql_connection.cursor()
        self.table_name_list = ["generator", "INJ", "EBT", "S02", "C2V", "BA1", "simulation"]

        # This dictionary is keyed by run-id and
        # the value is a string containing the deformatted dictionary of settings.
        # To see the deformatting function, go to deformat_dictionary(dict)

        self.run_id_settings_dict = self.construct_run_id_and_settings_dict_from_database()
        # print('time run_id_settings_dict = ', time.time() - start)
        # print(len(self.run_id_settings_dict))
        # exit()

    ## SHOULD SEPARATE THE FUNCTION BELOW OUT TO DEAL WITH:
    ## Machine area, Scan, Simulation tables separately.

    def create_dict_keys(self, dic, *keys):
        d = dic
        for k in keys:
            try:
                d[k]
            except:
                d[k] = {}
            d = d[k]
        return dic

    def construct_run_id_and_settings_dict_from_database(self):
        run_id_settings_dict = dict()
        for table_name in self.table_name_list:
            # start = time.time()
            sql = 'select run_id, component, parameter, value from '+table_name+''
            self.sql_cursor.execute(sql)
            settings_for_run_id = self.sql_cursor.fetchall()
            # print('time fetch ',table_name,' = ', time.time() - start)
            tmp = list(zip(*settings_for_run_id))
            tmp[-1] = map(ujson.loads, tmp[-1])
            settings_for_run_id = zip(*tmp)
            for run_id, component, parameter, value in settings_for_run_id:
                if component == 'null':
                    self.create_dict_keys(run_id_settings_dict, run_id, table_name, parameter)
                    run_id_settings_dict[run_id][table_name][parameter] = value
                else:
                    self.create_dict_keys(run_id_settings_dict, run_id, table_name, component, parameter)
                    run_id_settings_dict[run_id][table_name][component][parameter] = value
            # print('time ',table_name,' = ', time.time() - start)
        return run_id_settings_dict

    def compare_entries(self, yaml_settings):
        found_in_db = False
        run_id_for_settings = ''
        run_id = ''
        self.prepare_dict_for_checking(yaml_settings)
        for run_id, db_settings in self.run_id_settings_dict.items():
            if yaml_settings == db_settings:
                found_in_db = True
                run_id_for_settings = run_id
                return found_in_db, run_id
            else:
                continue
        return found_in_db, run_id

    def get_settings_dict_to_check(self, settings_to_save):
        settings_to_check = settings_to_save
        if 'scan' in settings_to_check:
           del settings_to_check['scan']
        return settings_to_check

    def prepare_dict_for_checking(self, settings_to_save):
        settings_to_check_dict = self.get_settings_dict_to_check(settings_to_save)

    def are_settings_in_database(self, yaml_settings):
        is_in_db, run_id = self.compare_entries(yaml_settings)
        return is_in_db

    def get_run_id_for_settings(self, yaml_settings):
        is_in_db, run_id = self.compare_entries(yaml_settings)
        return run_id

if __name__ == '__main__':
    db_reader = DatabaseReader()
    db_writer = database_writer.DatabaseWriter()
    settings_dict_to_save = yaml_parser.parse_parameter_input_file('scan_settings.yaml')
    ## WE WANT TO IGNORE THE SCAN SETTINGS BUT ALSO SAVE THEM INTO DB

    print('+++++ COMPARE +++++')
    if not db_reader.are_settings_in_database(settings_dict_to_save):
        print('Settings could not be found in DB, saving new settings')
        db_writer.save_dict_to_db(settings_dict_to_save)
    else:
        print('Settings can be found at: ', db_reader.get_run_id_for_settings(settings_dict_to_save))
