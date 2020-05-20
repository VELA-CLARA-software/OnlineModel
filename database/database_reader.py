import sys, os
import sqlite3
import uuid
import run_parameters_parser as yaml_parser
import collections
import json

class DatabaseReader():
	
	def __init__(self, *args, **kwargs):
		self.args = args
		self.kwargs = kwargs
		self.sql_connection = sqlite3.connect('SimulationDatabase.db')
		self.sql_cursor = self.sql_connection.cursor()



if __name__ == '__main__':
	db_creator = DatabaseReader()