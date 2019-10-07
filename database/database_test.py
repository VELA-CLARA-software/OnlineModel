import sys, os, shutil
import sqlite3
import uuid
import time
sys.path.append(os.path.dirname(os.path.dirname( os.path.abspath(__file__))))
import data.data as data

class Save_State():

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.conn = sqlite3.connect('astra_runner.db')
        self.cursor = self.conn.cursor()
        # connall.commit()

    def tempname(self):
        return str(uuid.uuid4())

    def create_state(self):
        name = self.tempname()
        while self.check_table_exists(name):
            name = self.tempname()
        date = time.time()
        sql = ''' INSERT INTO states(id, date)
              VALUES(?,?) '''
        print [name, date]
        self.cursor.execute(sql, [name, date, ])
        self.conn.commit()
        self.name = name
        return self.cursor.lastrowid

    def create_magnet_table(self, name):
        magnetdb = 'CREATE TABLE IF NOT EXISTS "magnets_'+name+'" ( \
            name TEXT,\
            parameter TEXT,\
            value REAL\
            );'
        self.cursor.execute(magnetdb)
        self.conn.commit()

    def check_table_exists(self, name):
        self.cursor.execute('SELECT count(*) FROM sqlite_master WHERE type="table" AND name="'+name+'";')
        return bool(self.cursor.fetchone()[0])

if __name__ == '__main__':
    state = Save_State()
    state.create_state()
