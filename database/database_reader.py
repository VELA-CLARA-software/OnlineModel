import sys, os
import sqlite3
import uuid
import run_parameters_parser as yaml_parser
import database_writer 
import collections
import json
from collections import defaultdict
## We can get rows back from SQL as a Row object
## This allows us to compare the yaml files and the DB entries more readily.


### Going to try and recreate the YAML python dictionary from DB, then we 
### can simply compare dictionaries when they are in the same form.

class DatabaseReader():
    
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.sql_connection = sqlite3.connect('SimulationDatabase.db')
        self.sql_cursor = self.sql_connection.cursor()
        self.sql_connection.row_factory = sqlite3.Row
        self.table_name_list = ["generator", "INJ", "EBT", "S02", "C2V", "BA1", "scan", "simulation"]
        self.table_run_id_dict = self.get_unique_run_id_and_table_dict()
        #self.yaml_filename = ''
        #self.yaml_dictionary = yaml_parser.parse_parameter_input_file(self.yaml_filename)
        #self.yaml_settings = self.deformat_dictionary(self.yaml_dictionary)
        
        
        # This dictionary is keyed by run-id and 
        # the value is a string containing the deformatted dictionary of settings.
        # To see the deformatting function, go to deformat_dictionary(dict)
        self.run_id_settings_dict = self.construct_run_id_and_settings_dict_from_database()


    def get_unique_run_id_and_table_dict(self):
        run_number_table_dict = defaultdict(list)
        for table_name in self.table_name_list:
            self.sql_cursor.execute('select DISTINCT run_id from ' + table_name)
            unique_run_id = self.sql_cursor.fetchall()
            if len(unique_run_id) > 0:
                for entry in range(0, len(unique_run_id)):
                    run_number_table_dict[table_name].append(unique_run_id[entry][0])
        return run_number_table_dict
    
    ## SHOULD SEPARATE THE FUNCTION BELOW OUT TO DEAL WITH: 
    ## Machine area, Scan, Simulation tables separately.
    
    def construct_run_id_and_settings_dict_from_database(self):
        run_id_settings_dict = defaultdict(dict)
        squashed_run_id_settings_dict = defaultdict(dict)
        for table_name, unique_runs in self.table_run_id_dict.items():
            for run_id in unique_runs:
                if table_name != 'scan' and table_name != 'simulation':
                    self.sql_cursor.execute('select component,parameter,value from ' + table_name + ' where run_id=\'' +run_id + '\'')
                    settings_for_run_id = self.sql_cursor.fetchall()
                    settings_dict = defaultdict(dict)
                    for component, parameter, value in settings_for_run_id:
                        settings_dict[component][parameter] = value
                        run_id_settings_dict[run_id][table_name] = settings_dict
                        squashed_run_id_settings_dict[run_id] = self.deformat_dictionary(run_id_settings_dict[run_id])
                elif table_name == 'scan':
                    self.sql_cursor.execute('select parameter,value from ' + table_name + ' where run_id=\'' +run_id + '\'')
                    settings_for_run_id = self.sql_cursor.fetchall()
                    settings_dict = defaultdict(dict)
                    for parameter, value in settings_for_run_id:
                        settings_dict[parameter] = value
                        run_id_settings_dict[run_id][table_name] = settings_dict
                        squashed_run_id_settings_dict[run_id] = self.deformat_dictionary(run_id_settings_dict[run_id])
                elif table_name == 'simulation':
                    self.sql_cursor.execute('select parameter, value from ' + table_name + ' where run_id=\''+run_id+'\'' + ' AND component=\'null\'')
                    settings_for_run_id = self.sql_cursor.fetchall()
                    settings_dict = defaultdict(dict)
                    for parameter, value in settings_for_run_id:
                        settings_dict[parameter] = value
                        run_id_settings_dict[run_id][table_name] = settings_dict
                        squashed_run_id_settings_dict[run_id] = self.deformat_dictionary(run_id_settings_dict[run_id])
                    self.sql_cursor.execute('select component, parameter, value from ' + table_name + ' where run_id=\''+run_id+'\'' + ' AND component!=\'null\'')
                    settings_for_run_id = self.sql_cursor.fetchall()
                    for component, parameter, value in settings_for_run_id:
                        settings_dict[component][parameter] = value
                        run_id_settings_dict[run_id][table_name] = settings_dict
                        squashed_run_id_settings_dict[run_id] = self.deformat_dictionary(run_id_settings_dict[run_id])
                        

        return squashed_run_id_settings_dict

    def compare_entries(self, yaml_settings):
        found_in_db = False
        run_id_for_settings = ''
        for run_id, db_settings in self.run_id_settings_dict.items():
            if yaml_settings == db_settings:
                found_in_db = True
                run_id_for_settings = run_id
            else:
                continue
        return found_in_db, run_id

    def pretty(self, d, indent=0):
       for key, value in d.items():
          print('  ' * indent + str(key))
          if isinstance(value, dict):
             self.pretty(value, indent+1)
          else:
             print('  ' * (indent+1) + str(value))

    def deformat_dictionary(self, dictionary_to_deformat):
        sorted_dict = dict(sorted(dictionary_to_deformat.items()))
        dict_dump = json.dumps(sorted_dict, sort_keys=True, indent=1)
        dict_dump = bytes(dict_dump, "utf-8").decode("unicode_escape")
        dict_dump = dict_dump.replace('"',"")
        dict_dump = dict_dump.replace("\n","")
        dict_dump = dict_dump.replace("null:{", "")
        dict_dump = "".join(dict_dump.split())
        return dict_dump

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
    print('+++++ COMPARE +++++')
    yaml_dump = db_reader.deformat_dictionary(settings_dict_to_save)
    if not db_reader.are_settings_in_database(yaml_dump):
        print('Settings could not be found in DB, saving new settings')
        db_writer.save_dict_to_db(settings_dict_to_save)
    else:
        print('Settings can be found at: ', db_reader.get_run_id_for_settings(yaml_dump))
        

