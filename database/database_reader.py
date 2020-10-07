import sys, os
sys.path.append(os.path.abspath(__file__+'/../../'))

import sys, os, time
import sqlite3
import uuid
import database.run_parameters_parser as yaml_parser
import database.database_writer
import data.lattices as lattices
import ujson as json
# import json
from collections import defaultdict, OrderedDict
## We can get rows back from SQL as a Row object
## This allows us to compare the yaml files and the DB entries more readily.


### Going to try and recreate the YAML python dictionary from DB, then we
### can simply compare dictionaries when they are in the same form.

class DatabaseReader():

    def __init__(self, database='SimulationDatabase.db', *args, **kwargs):
        start = time.time()
        self.args = args
        self.kwargs = kwargs
        self.database = database
        self.sql_connection = sqlite3.connect(self.database)
        self.sql_cursor = self.sql_connection.cursor()
        # List of lattice tables. This should be taken from a unified top-level controller at some point...
        self.table_name_list = ['generator'] + lattices.lattices

        # This dictionary is keyed by run-id and
        # the value is a string containing the deformatted dictionary of settings.
        # To see the deformatting function, go to deformat_dictionary(dict)
        print('###### Loading Database ######')
        self.lattice_id_settings_dict, self.run_id_settings_dict = self.construct_run_id_and_settings_dict_from_database()
        print('       time to load database = ', time.time() - start, 'seconds ')
        print('       Number of entries in database = ', len(self.run_id_settings_dict))
        print('###### Database Loaded ######')

    def update_lattice_tables_from_sql(self, table_name, lattice_id_settings_dict):
        """Take an SQL cursor and iteratively add elements to the lattice dictionary."""
        # It's faster to do this in chunks (not sure why, might be an SQLite issue?)
        chunk_size = 500000
        while True:
            start = time.time()
            settings_for_lattice_id = self.sql_cursor.fetchmany(chunk_size)
            # print('       time to execute LATTICE fetchmany = ', time.time() - start, 'seconds ')
            start = time.time()
            if not settings_for_lattice_id:
                # We've run out of data, so stop!
                break
            for run_id, component, parameter, value in settings_for_lattice_id:
                # Some tables don't use the component column, this will be 'null'
                if component == 'null':
                    lattice_id_settings_dict[run_id][table_name][parameter] = json.loads(value)
                else:
                    lattice_id_settings_dict[run_id][table_name][component][parameter] = json.loads(value)
            # print('       time to execute LATTICE dict update = ', time.time() - start, 'seconds ')

    def update_run_tables_from_sql(self, table_name, run_id_settings_dict):
        """Take an SQL cursor and iteratively add elements to the run dictionary."""
        settings_for_run_id = self.sql_cursor.fetchall()
        for run_id, prefix, start_lattice, directory in settings_for_run_id:
            run_id_settings_dict[run_id]['runs']['prefix'] = prefix
            run_id_settings_dict[run_id]['runs']['start_lattice'] = start_lattice
            run_id_settings_dict[run_id]['runs']['directory'] = directory

    def add_to_run_id_and_settings_dict_from_database(self, run_id):
        """Append a new run to the existing run and lattice dictionaries."""
        lattice_id_settings_dict = self.lattice_id_settings_dict
        run_id_settings_dict = self.run_id_settings_dict
        # For each of the lattice sections
        for table_name in self.table_name_list:
            # Load table rows from the DB given by the run_id
            sql = 'select run_id, component, parameter, value from \''+table_name+'\' where run_id = \'' + run_id + '\''
            self.sql_cursor.execute(sql)
            # Add the data to the dictionary
            self.update_lattice_tables_from_sql(table_name, lattice_id_settings_dict)
        # We need to do the same for the run table (which has a different format)
        sql = 'select run_id, prefix, start_lattice, directory from \'runs\' where run_id = \'' + run_id + '\''
        self.sql_cursor.execute(sql)
        self.update_run_tables_from_sql(table_name, run_id_settings_dict)

    def construct_run_id_and_settings_dict_from_database(self):
        """Construct the run and lattice dictionaries from the database entries."""
        # Create some dictionaries (sub-dictionaries will be created automagically)
        lattice_id_settings_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        run_id_settings_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        # For each of the lattice sections
        self.sql_start = time.time()
        for table_name in self.table_name_list:
            start = time.time()
            # Load table rows from the DB
            sql = 'select run_id, component, parameter, value from \''+table_name+'\''
            self.sql_cursor.execute(sql)
            # print('       time to execute LATTICE SQL = ', time.time() - start, 'seconds ')
            # Add the data to the dictionary
            self.update_lattice_tables_from_sql(table_name, lattice_id_settings_dict)
        # print('       time to update LATTICE TABLE = ', time.time() - start, 'seconds ')
        self.sql_start = time.time()
        # We need to do the same for the run table (which has a different format)
        sql = 'select run_id, prefix, start_lattice, directory from \'runs\''
        self.sql_cursor.execute(sql)
        # print('       time to execute RUN SQL = ', time.time() - self.sql_start, 'seconds ')
        self.update_run_tables_from_sql(table_name, run_id_settings_dict)
        # print('       time to update RUN TABLE = ', time.time() - self.sql_start, 'seconds ')

        return lattice_id_settings_dict, run_id_settings_dict

    def findDiff(self, d1, d2, path=""):
        """Compare two dictionaries and print the differences."""
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
        """Compare enties between an input YAML dictionary and the database to find a match."""
        found_in_db = False
        run_id_for_settings = ''
        run_id = ''
        yaml_settings = self.prepare_dict_for_checking(yaml_settings)
        # Compare each lattice to the input yaml file and return true if they match
        # for run_id, db_settings in self.lattice_id_settings_dict.items():
        #     if yaml_settings == db_settings:
        #         found_in_db = True
        #         run_id_for_settings = run_id
        #         return found_in_db, run_id
        # If they didn't match, it may be because it is not a full run, so find the nearest match using the prefix runs
        # start = time.time()
        found_run_id, lattices = self.find_lattices_that_dont_exist(yaml_settings)
        # print('Check exists time = ', time.time() - start)
        # If there was a full match the function returns [run_id, None]
        # We do a double check: run_id is not False (which would be No match) and the lattices is None (nothing to re-run)
        if found_run_id is not False and lattices is None:
            # We have found a full match, so return the run_id of the match
            found_in_db = True
            run_id = found_run_id
        return found_in_db, run_id

    def check_settings_including_prefix(self, run_id, yaml_settings, table):
        """"Recursively search a tracking run and it's prefix's for a match."""
        # These are the settings from the DB we are checking
        db_settings = self.lattice_id_settings_dict[run_id]
        # position of the table we are investigating
        table_idx = self.table_name_list.index(table)
        # Do the setting's exist? Remember that if we used a prefix, onlt new settings were saved, so this might be False
        settings_exist = (table in db_settings and yaml_settings[table] == db_settings[table])
        if settings_exist:
            # We found a match!
            return settings_exist
        # We didn't find a match, but maybe it is in the prefix run?
        run_id_prefix = self.run_id_settings_dict[run_id]['runs']['prefix']
        if run_id_prefix is not None:
            # We have a prefix, so we need to search it
            # Find which lattice this run starts from - if the table is before the current run, we need to search the prefix as well
            start_lattice_idx = self.table_name_list.index(self.run_id_settings_dict[run_id]['runs']['start_lattice'])
            if  table_idx < start_lattice_idx:
                # We need to search the prefix, so recursively do it
                return self.check_settings_including_prefix(run_id_prefix, yaml_settings, table)
            else:
                # The table we are looking at is in this track (not the prefix) and we already tested this above (we know it will be False by deduction)
                return settings_exist
        else:
            return False

    def find_lattices_that_dont_exist(self, yaml_settings):
        """Find the closest match to an input file and return the run_id and the non-matching lattice sections."""
        lattice_exists = OrderedDict()
        # Default answer (equates to run everything)
        null_result = [False, self.table_name_list]
        # iterate through the database entries
        for run_id in self.lattice_id_settings_dict.keys():
            # comparison on each lattice and each run_id
            lattice_exists[run_id] = []
            for table in self.table_name_list:
                # Check if the lattice matches recursively through any prefix tracking runs
                settings_exist = self.check_settings_including_prefix(run_id, yaml_settings, table)
                if not settings_exist:
                    # if we don't get a true, we can stop as we don't care after a False
                    break
                else:
                    # Append the true to the list. We will count these to determine which lattice we need to start from
                    lattice_exists[run_id].append(settings_exist)
        # if the DB is empty, we need to run everything so return the default
        if len(lattice_exists) > 0:
            # Count the trues (lattice matches) in each entry in the DB
            most_trues = [len(x) for x in lattice_exists.values()]
            # Find where this occurs
            idx_most_trues = most_trues.index(max(most_trues))
            # Return the lattice_exists entry with the most trues (this is ugly!?)
            result = list(list(lattice_exists.items())[idx_most_trues])
            # Since we are in order of lattice name, we can find the starting lattice based on the length of True's
            idx_start_lattice = len(result[1])
            if idx_start_lattice == 0:
                # If we have to re-run all lattices, return the null result
                return null_result
            elif idx_start_lattice < len(self.table_name_list):
                # If we have a partial result, set the lattice's that need to be run based on missing True's
                result[-1] = self.table_name_list[idx_start_lattice:]
            else:
                # Or if we have a full match, set the lattice's that need to be run to None
                result[-1] = None
            return result
        else:
            return null_result

    def get_run_id_for_lattice(self, run_id, t):
            table_idx = self.table_name_list.index(t)
            if self.run_id_settings_dict[run_id]['runs']['prefix'] is not None:
                start_lattice_idx = self.table_name_list.index(self.run_id_settings_dict[run_id]['runs']['start_lattice'])
                if  table_idx < start_lattice_idx:
                    return self.get_run_id_for_lattice(self.run_id_settings_dict[run_id]['runs']['prefix'], t)
            return os.path.relpath(self.run_id_settings_dict[run_id]['runs']['directory'])

    def get_run_id_for_each_lattice(self, run_id=''):
        """For each lattice, find the corresponding run_id taking into account prefix runs"""
        result = {}
        for t in self.table_name_list:
            result[t] = self.get_run_id_for_lattice(run_id, t)
        return result

    def get_settings_dict_to_check(self, settings_to_save):
        """Create a lattice dictionary from the input settings."""
        settings_to_check = {}
        # We only want to lattice information for the dictionary!
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
        """Find if settings exist in the DB."""
        is_in_db, run_id = self.compare_entries(yaml_settings)
        return is_in_db

    def get_run_id_for_settings(self, yaml_settings):
        """Find the run_id for settings from the DB."""
        is_in_db, run_id = self.compare_entries(yaml_settings)
        return run_id

    def get_all_run_ids(self):
        return self.run_id_settings_dict.keys()

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
