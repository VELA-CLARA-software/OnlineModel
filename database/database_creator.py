import sys, os
import sqlite3
import uuid
import collections
import json

class DatabaseCreator():

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.sql_connection = sqlite3.connect('SimulationDatabase.db')
        self.sql_cursor = self.sql_connection.cursor()

    def create_simulation_database(self, clean=False, tables=None):
        if tables is None:
            tables = ['generator', 'INJ', 'EBT', 'S02', 'C2V', 'BA1', 'simulation', 'scan', 'runs']
        elif not isinstance(tables, (list, tuple)) and isinstance(tables, str):
            tables = [tables]
        else:
            tables = []
        for t in tables:
            if t == 'runs':
                self.create_runs_table(clean)
            elif t == 'scan':
                self.create_scan_table(clean)
            else:
                self.create_table(t, clean)

    def create_runs_table(self, clean=False):
        sql = '''CREATE TABLE IF NOT EXISTS "runs" (
                	"run_id"	TEXT UNIQUE,
                	"timestamp"	TEXT,
                	"username"	TEXT
                );'''
        self.sql_cursor.execute(sql)
        if clean:
            sql = 'delete from RUNS;'
            self.sql_cursor.execute(sql)
        self.sql_connection.commit()

    def create_scan_table(self, clean=False):
        sql = '''CREATE TABLE IF NOT EXISTS "scan" (
                	"run_id"	TEXT,
                	"area"	TEXT,
                	"component"	TEXT,
                	"parameter"	TEXT,
                	"start"	TEXT,
                	"stop"	TEXT,
                	"step"	TEXT,
                	"value"	TEXT
                );'''
        self.sql_cursor.execute(sql)
        if clean:
            sql = 'delete from SCAN;'
            self.sql_cursor.execute(sql)
        self.sql_connection.commit()


    def create_table(self, table_name, clean=False):
        sql = 'CREATE TABLE IF NOT EXISTS "' + table_name +'" ( \
            run_id TEXT,\
            component TEXT,\
            parameter TEXT,\
            value TEXT\
            );'
        self.sql_cursor.execute(sql)
        if clean:
            sql = 'delete from ' + table_name + ';'
            self.sql_cursor.execute(sql)
        self.sql_connection.commit()

if __name__ == '__main__':
    def str2bool(v):
        if isinstance(v, bool):
           return v
        if v.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Boolean value expected.')

    import argparse
    parser = argparse.ArgumentParser(description='Create simulation database')
    parser.add_argument('--clean', const=True, default=False, type=str2bool, nargs='?')
    args = parser.parse_args()
    db_creator = DatabaseCreator()
    db_creator.create_simulation_database(clean=args.clean)
