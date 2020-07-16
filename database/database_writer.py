# -*- coding: utf-8 -*-
import sys, os
import sqlite3
import uuid
import database.run_parameters_parser as yaml_parser
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

    def save_dict_to_db(self, settings_dict_to_save, run_id=None):
        ### NEEDS TO CHECK THE STATE OF RESULTS IN TABLE ###
        ### AS SOON AS AN ENTRY DOES NOT EXIST, WRITE IT TO TABLE ###
        # converting the dictionary to flattened form to save to db
        newdict = self.flatten(settings_dict_to_save)
        # creating a new run_id with uuid IF NOT passed to function
        if run_id is None:
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
                # print('---------------------------------')
                # print('Machine Area: ', table_name)
                # print('Component: ', component)
                # print('Parameter: ', parameter)
                # print('Value: ', value)
                # print('---------------------------------')
                self.save_entry_to_machine_area_table(run_id, table_name, component, parameter, value)
            if (table_name == 'simulation'):
                if len(splitstr) < 2:
                    parameter = splitstr[0]
                    value = v
                    component = json.dumps(None)
                else:
                    component = splitstr[0]
                    parameter = splitstr[1]
                    value = v
                self.save_entry_to_simulation_table(run_id, component, parameter, value)

        # scan dictionary is now treated differently, so it is run separately
        if 'scan' in settings_dict_to_save:
            self.save_entry_to_scan_table(run_id, settings_dict_to_save['scan'])

        # commit the changes
        self.sql_connection.commit()

    def save_entry_to_machine_area_table(self, run_id, table_name, component, parameter, value):
        columnstring = '(run_id,component,parameter,value)'
        valuestring =  '(?, ?, ?, ?)'
        sql = ''' INSERT INTO ''' + table_name + ''' '''+columnstring+'''
               VALUES''' + valuestring
        self.sql_cursor.execute(sql, [run_id] + [component] + [parameter] + [json.dumps(value)])

    def split_accessible_name(self, aname):
        if len((aname.split(':'))) == 3:
            dictname, pv, param = map(str, aname.split(':'))
        else:
            param = None
            dictname, pv = map(str, aname.split(':'))
        return dictname, pv, param

    def save_entry_to_scan_table(self, run_id, scandict):
        step = scandict['parameter_scan_step_size']
        start = scandict['parameter_scan_from_value']
        stop = scandict['parameter_scan_to_value']
        value = scandict['value']
        area, component, parameter = self.split_accessible_name(scandict['parameter'])
        columnstring = '(run_id, area, component, parameter, start, stop, step, value)'
        valuestring = '(?,?,?,?,?,?,?,?)'
        sql = '''INSERT INTO scan ''' + columnstring + ''' VALUES ''' + valuestring
        self.sql_cursor.execute(sql, [run_id, area, component, parameter, start, stop, step, value])

    def save_entry_to_simulation_table(self, run_id, component, parameter, value):
        columnstring = '(run_id, component, parameter, value)'
        valuestring = '(?,?,?,?)'
        sql = '''INSERT INTO simulation ''' + columnstring + '''VALUES''' + valuestring
        self.sql_cursor.execute(sql, [run_id] + [component] + [parameter] + [json.dumps(value)])

    def save_entry_to_run_table(self, run_id, timestamp, user):
        columnstring = '(run_id, timestamp, username)'
        valuestring = '(?,?,?)'
        sql = '''INSERT OR IGNORE INTO runs ''' + columnstring + '''VALUES''' + valuestring
        self.sql_cursor.execute(sql, [run_id, timestamp, user])
        self.sql_connection.commit()


if __name__ == '__main__':
    db_writer = DatabaseWriter()
    settings_dict_to_save = yaml_parser.parse_parameter_input_file('scan_settings.yaml')
    db_writer.save_dict_to_db(settings_dict_to_save)
