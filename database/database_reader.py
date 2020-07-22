import sys, os, time
import sqlite3
import uuid
import database.run_parameters_parser as yaml_parser
import database.database_writer
import ujson as json
# import json
from collections import defaultdict, OrderedDict
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
        self.table_name_list = ["generator", "INJ", "CLA-S02", "CLA-C2V", "EBT-INJ", "EBT-BA1"]

        # This dictionary is keyed by run-id and
        # the value is a string containing the deformatted dictionary of settings.
        # To see the deformatting function, go to deformat_dictionary(dict)
        print('###### Loading Database ######')
        self.lattice_id_settings_dict, self.run_id_settings_dict = self.construct_run_id_and_settings_dict_from_database()
        print('       time to load database = ', time.time() - start, 'seconds ')
        print('       Number of entries in database = ', len(self.run_id_settings_dict))
        print('###### Database Loaded ######')
        # exit()

    ## SHOULD SEPARATE THE FUNCTION BELOW OUT TO DEAL WITH:
    ## Machine area, Scan, Simulation tables separately.

    def update_lattice_tables_from_sql(self, table_name, lattice_id_settings_dict):
        chunk_size = 5000000
        while True:
            settings_for_lattice_id = self.sql_cursor.fetchmany(chunk_size)
            if not settings_for_lattice_id:
                break
            for run_id, component, parameter, value in settings_for_lattice_id:
                if component == 'null':
                    lattice_id_settings_dict[run_id][table_name][parameter] = json.loads(value)
                else:
                    lattice_id_settings_dict[run_id][table_name][component][parameter] = json.loads(value)

    def update_run_tables_from_sql(self, table_name, run_id_settings_dict):
        settings_for_run_id = self.sql_cursor.fetchall()
        for run_id, prefix, start_lattice in settings_for_run_id:
            run_id_settings_dict[run_id]['runs']['prefix'] = prefix
            run_id_settings_dict[run_id]['runs']['start_lattice'] = start_lattice

    def add_to_run_id_and_settings_dict_from_database(self, run_id):
        lattice_id_settings_dict = self.lattice_id_settings_dict
        run_id_settings_dict = self.run_id_settings_dict
        for table_name in self.table_name_list:
            sql = 'select run_id, component, parameter, value from \''+table_name+'\' where run_id = \'' + run_id + '\''
            self.sql_cursor.execute(sql)
            self.update_lattice_tables_from_sql(table_name, lattice_id_settings_dict)
        sql = 'select run_id, prefix, start_lattice from \'runs\' where run_id = \'' + run_id + '\''
        self.sql_cursor.execute(sql)
        self.update_run_tables_from_sql(table_name, run_id_settings_dict)

    def construct_run_id_and_settings_dict_from_database(self):
        lattice_id_settings_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        run_id_settings_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        for table_name in self.table_name_list:
            # print('loading table ', table_name)
            sql = 'select run_id, component, parameter, value from \''+table_name+'\''
            self.sql_cursor.execute(sql)
            self.update_lattice_tables_from_sql(table_name, lattice_id_settings_dict)
        sql = 'select run_id, prefix, start_lattice from \'runs\''
        self.sql_cursor.execute(sql)
        self.update_run_tables_from_sql(table_name, run_id_settings_dict)

        return lattice_id_settings_dict, run_id_settings_dict

    def findDiff(self, d1, d2, path=""):
        for k in d1:
            if (k not in d2):
                print ('findDiff:', path, ":")
                print ('findDiff:', k + " as key not in d2", "\n")
            else:
                if type(d1[k]) is dict:
                    if path == "":
                        path = k
                    else:
                        path = path + "->" + k
                    self.findDiff(d1[k],d2[k], path)
                else:
                    if d1[k] != d2[k]:
                        print('findDiff:', path+":"+k,':',d1[k],'=!=',d2[k])

    def compare_entries(self, yaml_settings):
        found_in_db = False
        run_id_for_settings = ''
        run_id = ''
        yaml_settings = self.prepare_dict_for_checking(yaml_settings)
        lattice_exists = OrderedDict()
        for run_id, db_settings in self.lattice_id_settings_dict.items():
            if yaml_settings == db_settings:
                found_in_db = True
                run_id_for_settings = run_id
                # print('compare_entries: found db entry exists')
                return found_in_db, run_id
        found_run_id, lattices = self.find_lattices_that_dont_exist(yaml_settings)
        # print('compare entries:', found_run_id, lattices)
        if not found_run_id is False and lattices == []:
            # print('compare_entries: Found all entries = ', found_run_id)
            found_in_db = True
            run_id = found_run_id
        return found_in_db, run_id

    def check_settings_including_prefix(self, run_id, yaml_settings, table):
        db_settings = self.lattice_id_settings_dict[run_id]
        table_idx = self.table_name_list.index(table)
        settings_exist = (table in db_settings and yaml_settings[table] == db_settings[table])
        run_id_prefix = self.run_id_settings_dict[run_id]['runs']['prefix']
        if settings_exist:
            return settings_exist
        elif run_id_prefix is not None:
            start_lattice_idx = self.table_name_list.index(self.run_id_settings_dict[run_id]['runs']['start_lattice'])
            if  table_idx < start_lattice_idx:
                return self.check_settings_including_prefix(run_id_prefix, yaml_settings, table)
            else:
                prefix_settings_exist = (yaml_settings[table] == db_settings[table])
                return prefix_settings_exist
        else:
            return False

    def count_trues(self, x):
        return x.index(False) if False in x else len(x)

    def find_lattices_that_dont_exist(self, yaml_settings):
        lattice_exists = OrderedDict()
        result = [False, self.table_name_list]
        for run_id in self.lattice_id_settings_dict.keys():
            # comparison on each lattice and each run_id
            lattice_exists[run_id] = []
            for table in self.table_name_list:
                settings_exist = self.check_settings_including_prefix(run_id, yaml_settings, table)
                if not settings_exist:
                    break
                else:
                    lattice_exists[run_id].append(settings_exist)
        if len(lattice_exists) > 0:
            most_trues = [self.count_trues(x) for x in lattice_exists.values()]
            idx_most_trues = most_trues.index(max(most_trues))
            most_true = list(list(lattice_exists.items())[idx_most_trues])
            result = most_true
            idx_start_lattice = len(most_true[1])
            if idx_start_lattice < len(self.table_name_list) and idx_start_lattice > 0:
                result[-1] = self.table_name_list[idx_start_lattice:]
            else:
                result[-1] = []
        return result

    def get_settings_dict_to_check(self, settings_to_save):
        settings_to_check = {}
        for table in self.table_name_list:
            settings_to_check[table] = settings_to_save[table]
        # if 'scan' in settings_to_check:
        #    del settings_to_check['scan']
        # if 'runs' in settings_to_check:
        #    del settings_to_check['runs']
        return settings_to_check

    def prepare_dict_for_checking(self, settings_to_save):
        return self.get_settings_dict_to_check(settings_to_save)

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
