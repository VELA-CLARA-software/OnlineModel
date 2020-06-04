import sys, os
import sqlite3
import uuid
import run_parameters_parser as yaml_parser
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
        self.run_id_settings_dict = self.construct_run_id_and_settings_dict_from_database()


    def get_unique_run_id_and_table_dict(self):
        run_number_table_dict = defaultdict(list)
        for table_name in self.table_name_list:
            self.sql_cursor.execute('select DISTINCT run_id from ' + table_name)
            unique_run_id = self.sql_cursor.fetchall()
            if len(unique_run_id) > 0:
                run_number_table_dict[table_name].append(unique_run_id[0][0])
        return run_number_table_dict
    
    def construct_run_id_and_settings_dict_from_database(self):
        run_id_settings_dict = defaultdict(dict)
        for table_name, unique_runs in self.table_run_id_dict.items():
            for run_id in unique_runs:
                self.sql_cursor.execute('select component,parameter,value from ' + table_name + ' where run_id=\'' +run_id + '\'')
                settings_for_run_id = self.sql_cursor.fetchall()
                settings_dict = defaultdict(dict)
                for component, parameter, value in settings_for_run_id:
                    settings_dict[component][parameter] = value
                    run_id_settings_dict[run_id][table_name] = settings_dict
        return run_id_settings_dict

    # def compare_database_dict_with_yaml_dict(self, yaml_dict):
        # sorted_yaml_dict = sorted(yaml_dict)
        # sorted_run_id_dict = sorted(self.run_id_settings_dict)
        # for run_id in sorted_run_id_dict.keys():
            # if (sorted_yaml_dict == sorted_run_id_dict[run_id])):
                # print("Results for settings can be found at: ", run_id)
                # return

    def pretty(self, d, indent=0):
       for key, value in d.items():
          print('  ' * indent + str(key))
          if isinstance(value, dict):
             self.pretty(value, indent+1)
          else:
             print('  ' * (indent+1) + str(value))

if __name__ == '__main__':
    db_creator = DatabaseReader()
    table_run_id_dict = db_creator.get_unique_run_id_and_table_dict()
    settings_dict_to_save = yaml_parser.parse_parameter_input_file('scan_settings.yaml')
    print(table_run_id_dict)
    run_id_settings_dict = db_creator.run_id_settings_dict
    # print("+++++++++  DATABASE ++++++++++++")
    # db_creator.pretty(run_id_settings_dict['6660535c-91f4-4579-b074-1edc01e747f5'])
    # print("+++++++++  YAML ++++++++++++")
    # db_creator.pretty(settings_dict_to_save)
    
    
    print('+++++ COMPARE +++++')
    sorted_yaml_dict = sorted(settings_dict_to_save.items())
    sorted_run_id_settings_dict = sorted(run_id_settings_dict['6660535c-91f4-4579-b074-1edc01e747f5'].items())
    print("SORTED YAML DICT: ", sorted_yaml_dict)
    print("SORTED DB SETTINGS: ", sorted_run_id_settings_dict)
    if (sorted_yaml_dict == sorted_run_id_settings_dict):
        print("Settings can be found : '6660535c-91f4-4579-b074-1edc01e747f5'")
    else:
        print("Settings could not be found in DB")
        print("Mismatched Items: ", sorted_yaml_dict & sorted_run_id_settings_dict)
    ##### Now recreate the settings dict per run_number:
    ##### select * from table_name WHERE run_id = table_run_id_dict[table_name]
    #### and split up row into the form: table_name : {parameter_name : value}
    #### we can then have a full dictionary keyed by run_id: {run_id : {table_name : {parameter_name : value} } }
    
            # settings_entry_dict[table_name].append(tuple(item[1:]))
            # print(item)
    # run_entry_dict[row[0]] = settings_entry_dict
    # for key, value in run_entry_dict.items():
            # print("KEY: ", key, " VALUE: ", value, "\n")
            # print("")
