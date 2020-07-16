import sys, os
import sqlite3
import uuid
import database.run_parameters_parser as yaml_parser
import collections
import json

class DatabaseCreator():

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.sql_connection = sqlite3.connect('SimulationDatabase.db')
        self.sql_cursor = self.sql_connection.cursor()

    def create_simulation_database(self):
        self.create_table('generator')
        self.create_table('INJ')
        self.create_table('EBT')
        self.create_table('S02')
        self.create_table('C2V')
        self.create_table('BA1')
        self.create_table('simulation')
        #### NEED TO HAVE THE SAME COLUMNS AND WRITE None TO THEM IF EMPTY.
        self.create_runs_table()
        self.create_scan_table()

    def create_runs_table(self):
        sql = '''CREATE TABLE "runs" (
                	"run_id"	TEXT UNIQUE,
                	"timestamp"	TEXT,
                	"username"	TEXT
                );'''
        self.sql_cursor.execute(sql)
        sql = 'delete from RUNS;'
        self.sql_cursor.execute(sql)
        self.sql_connection.commit()

    def create_scan_table(self):
        sql = '''CREATE TABLE "scan" (
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
        sql = 'delete from SCAN;'
        self.sql_cursor.execute(sql)
        self.sql_connection.commit()


    def create_table(self, table_name):
        sql = 'CREATE TABLE IF NOT EXISTS "' + table_name +'" ( \
            run_id TEXT,\
            component TEXT,\
            parameter TEXT,\
            value TEXT\
            );'
        self.sql_cursor.execute(sql)
        sql = 'delete from ' + table_name + ';'
        self.sql_cursor.execute(sql)
        self.sql_connection.commit()

if __name__ == '__main__':
    db_creator = DatabaseCreator()
    db_creator.create_simulation_database()
