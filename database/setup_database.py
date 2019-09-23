import sys, os, shutil
import sqlite3
sys.path.append(os.path.dirname(os.path.dirname( os.path.abspath(__file__))))
import data.data as data


magnetdb = 'CREATE TABLE IF NOT EXISTS "magnets" ( \
    name varchar(200),\
    k1l int(100),\
    length int(100)\
    );'

connall = sqlite3.connect('astra_runner.db')
setsdball = connall.cursor()
setsdball.execute(magnetdb)
connall.commit()
