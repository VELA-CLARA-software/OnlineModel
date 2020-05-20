import sys, os
import sqlite3
import uuid
import run_parameters_parser as yaml_parser
import collections
import json

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



if __name__ == '__main__':
    db_creator = DatabaseReader()
    db_creator.sql_connection.row_factory = sqlite3.Row
    db_creator.sql_cursor.execute('select * from BA1')
    row = db_creator.sql_cursor.fetchall()
    column_names = list()
    for index in range(0,4):
        column_names.append(db_creator.sql_cursor.description[index][0])
    print(column_names)
    print(type(row))
    print(len(row))
    unique_entry_dict = dict()
    for item in row:
        print(item)
    print(unique_entry_dict)