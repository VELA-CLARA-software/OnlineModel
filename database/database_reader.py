import sys, os, time
import sqlite3
import uuid
import database.run_parameters_parser as yaml_parser
import database.database_writer
import collections
import ujson as json
# import json
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
        print('###### Loading Database ######')
        self.run_id_settings_dict = self.construct_run_id_and_settings_dict_from_database()
        print('       time to load database = ', time.time() - start, 'seconds ')
        print('       Number of entries in database = ', len(self.run_id_settings_dict))
        print('###### Database Loaded ######')
        # exit()

    ## SHOULD SEPARATE THE FUNCTION BELOW OUT TO DEAL WITH:
    ## Machine area, Scan, Simulation tables separately.

    def update_from_sql(self, table_name, run_id_settings_dict):
        chunk_size = 5000000
        while True:
            settings_for_run_id = self.sql_cursor.fetchmany(chunk_size)
            if not settings_for_run_id:
                break
            for run_id, component, parameter, value in settings_for_run_id:
                if component == 'null':
                    run_id_settings_dict[run_id][table_name][parameter] = json.loads(value)
                else:
                    run_id_settings_dict[run_id][table_name][component][parameter] = json.loads(value)

    def add_to_run_id_and_settings_dict_from_database(self, run_id):
        run_id_settings_dict = self.run_id_settings_dict
        for table_name in self.table_name_list:
            sql = 'select run_id, component, parameter, value from '+table_name+' where run_id = \'' + run_id + '\''
            self.sql_cursor.execute(sql)
            self.update_from_sql(table_name, run_id_settings_dict)

    def construct_run_id_and_settings_dict_from_database(self, run_id=None):
        run_id_settings_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        for table_name in self.table_name_list:
            # start = time.time()
            sql = 'select run_id, component, parameter, value from '+table_name+''
            if run_id is not None:
                sql += ' where run_id = \'' + run_id + '\''
            self.sql_cursor.execute(sql)
            self.update_from_sql(table_name, run_id_settings_dict)
        return run_id_settings_dict

    def findDiff(self, d1, d2, path=""):
        for k in d1:
            if (k not in d2):
                print (path, ":")
                print (k + " as key not in d2", "\n")
            else:
                if type(d1[k]) is dict:
                    if path == "":
                        path = k
                    else:
                        path = path + "->" + k
                    self.findDiff(d1[k],d2[k], path)
                else:
                    if d1[k] != d2[k]:
                        self.differences += 1

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
                # self.differences = 0
                # self.findDiff(yaml_settings, db_settings)
                # print(run_id, self.differences)
                continue
        return found_in_db, run_id

    def get_settings_dict_to_check(self, settings_to_save):
        settings_to_check = settings_to_save
        if 'scan' in settings_to_check:
           del settings_to_check['scan']
        if 'runs' in settings_to_check:
           del settings_to_check['runs']
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
