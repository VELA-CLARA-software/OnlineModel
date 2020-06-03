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

    def get_unique_run_id_and_table_dict(self):
        run_number_table_dict = defaultdict(list)
        for table_name in self.table_name_list:
            self.sql_cursor.execute('select DISTINCT run_id from ' + table_name)
            unique_run_id = self.sql_cursor.fetchall()
            if len(unique_run_id) > 0:
                run_number_table_dict[table_name].append(unique_run_id[0][0])
        return run_number_table_dict

if __name__ == '__main__':
    db_creator = DatabaseReader()
    table_run_id_dict = db_creator.get_unique_run_id_and_table_dict()
    print(table_run_id_dict)
    run_id_settings_dict = defaultdict(list)
    for table_name, unique_runs in table_run_id_dict.items():
        for run_id in unique_runs:
            db_creator.sql_cursor.execute('select * from ' + table_name + ' where run_id=\'' +run_id + '\'')
            settings_for_run_id = db_creator.sql_cursor.fetchall()
            run_id_settings_dict[run_id][table_name].append(settings_for_run_id[run_id])
    print(run_id_settings_dict)
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
