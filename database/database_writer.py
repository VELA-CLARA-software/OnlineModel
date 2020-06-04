# -*- coding: utf-8 -*-

import sys, os
import sqlite3
import uuid
import run_parameters_parser as yaml_parser
import collections
import json

class DatabaseWriter():
    
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.sql_connection = sqlite3.connect('SimulationDatabase.db')
        self.sql_cursor = self.sql_connection.cursor()

    def tempname(self):
        return str(uuid.uuid4())

    def flatten(self, d, parent_key='', sep='£'):
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, collections.MutableMapping):
                items.extend(self.flatten(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def save_dict_to_db(self, settings_dict_to_save):
        ### NEEDS TO CHECK THE STATE OF RESULTS IN TABLE ###
        ### AS SOON AS AN ENTRY DOES NOT EXIST, WRITE IT TO TABLE ###
        
        # converting the dictionary to flattened form to save to db
        newdict = self.flatten(settings_dict_to_save)
        # creating a new run_id with uuid
        run_id = self.tempname()
        # cycle through flattened dictionary key/value pairs
        # Flattened Format: <TABLE_NAME>£<HARDWARE_NAME>£<PARAMETER> : <VALUE>
        # Example: BA1£EBT-BA1-MAG-QUAD-01£kl1 : -0.959
        for k,v in newdict.items():
            splitstr = k.split('£')
            table_name = splitstr[0]
            splitstr.remove(table_name)
            if (table_name != 'scan' and table_name != 'simulation'):
                component = splitstr[0]
                parameter = splitstr[1]
                value = v
                print('---------------------------------')
                print('Machine Area: ', table_name)
                print('Component: ', component)
                print('Parameter: ', parameter)
                print('Value: ', value)
                print('---------------------------------')
                self.save_entry_to_machine_area_table(run_id, table_name, component, parameter, value)
        self.sql_connection.commit()


    def save_entry_to_runs_table(self, runno, area, directory):
        if (self.check_entry_in_runs_table(runno, area, directory)):
            print("NOT SAVING TO RUN TABLE")
        else:
            print("SAVING TO RUN TABLE")
            print("RUN NUMBER: ", runno, " AREA: ", area,  " DIRECTORY: ", directory)
            run_columnstring = '(runnumber, area, directory)'
            run_valuestring = '(?,?,?)'
            run_sql = '''INSERT INTO runs '''+run_columnstring+''' VALUES '''+run_valuestring
            self.cursor.execute(run_sql, [runno,area,directory])
            self.conn.commit()

    def save_entry_to_machine_area_table(self, run_id, table_name, component, parameter, value):
        columnstring = '(run_id,component,parameter,value)'
        valuestring =  '(?, ?, ?, ?)'
        sql = ''' INSERT INTO ''' + table_name + ''' '''+columnstring+'''
               VALUES''' + valuestring
        self.sql_cursor.execute(sql, [run_id] + [component] + [parameter] + [json.dumps(value)])



    def save_entry_to_scan_table(self, runno, data, values):
        columnstring = '(runnumber, name, parameter, value)'
        valuestring = '(?,?,?,?)'
        if (len(data) < 2):
            data.insert(0,None)
        sql = '''INSERT INTO scan ''' + columnstring + ''' VALUES ''' + valuestring
        self.cursor.execute(sql, [runno] + data + [json.dumps(values)])


    def save_entry_to_simulation_table(self, runno, data, values):
        columnstring = '(runnumber, name, parameter, value)'
        if (len(data) < 2):
            data.append(json.dumps(None))
        valuestring = '(?,' + ','.join(['?' for i in range(len(data)+1)]) + ')'
        sql = '''INSERT INTO simulation ''' + columnstring + '''VALUES''' + valuestring
        self.cursor.execute(sql, [runno] + data + [json.dumps(values)])




if __name__ == '__main__':
    db_writer = DatabaseWriter()
    settings_dict_to_save = yaml_parser.parse_parameter_input_file('scan_settings.yaml')
    db_writer.save_dict_to_db(settings_dict_to_save)