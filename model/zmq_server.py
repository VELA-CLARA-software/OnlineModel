import os, sys
import time
import zmq
import threading
import signal
import server_model as model
import logging
import json
import uuid
from copy import deepcopy

format = "%(asctime)s: %(message)s"
logging.basicConfig(format=format, level=logging.INFO,
                    datefmt="%H:%M:%S")

class Data(object):

    def __init__(self):
        super(Data, self).__init__()

class modelThread(threading.Thread):

    def __init__(self, msg, runno, directoryname):
        super(modelThread, self).__init__()
        self.data = Data()
        for k,v in msg.items():
            if isinstance(v,dict):
                setattr(self.data,k,v.copy())
            else:
                setattr(self.data,k,v)
        self.runno = runno
        self.directoryname = directoryname
        self.track_model = model.Model(directoryname=self.directoryname, data=self.data, runno=self.runno)
        # self.status = ""

    def run(self):
        logging.info("Thread %s: starting", self.runno)
        # self.status = "\ttracking..."
        self.track_model.run_script()
        logging.info("Thread %s: finishing", self.runno)
        # self.status = "finished"

    def status(self):
        return self.track_model.Framework.progress if self.track_model.Framework.progress < 100 else "finished"

class zmqServer():

    def __init__(self, port=8192):
        super(zmqServer, self).__init__()
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.port = port
        self.status = ""
        self.thread_objects = {}
        self.dirnames = self.load_dirnames_from_json()
        print(self.dirnames)

    def get_next_runno(self):
        return next(i for i, e in enumerate(sorted(self.dirnames.keys()) + [ None ], 1) if i != e)

    def run(self):
        print('Server starting on port:', self.port)
        self.socket.bind("tcp://*:%s" % (self.port))
        while True:
            msg = self.socket.recv_pyobj()
            if isinstance(msg, list) and msg[0] == 'data dictionary':
                runno = self.start_tracking_run(*msg)
                self.socket.send_pyobj(runno)
            elif isinstance(msg, list) and msg[0] == 'status':
                self.socket.send_pyobj(self.get_status_message(*msg))
            elif isinstance(msg, list) and msg[0] == 'directoryname':
                self.socket.send_pyobj(self.dirnames[msg[1]])
            elif msg == 'hello':
                self.socket.send_pyobj("hello from the server")
            else:
                self.socket.send_pyobj('Tick')

    def start_tracking_run(self, type, datadict):
        runno = self.get_next_runno()
        print('runno = ', runno)
        directoryname = self.create_random_directory_name(runno)
        thread = modelThread(datadict, runno, directoryname)
        self.thread_objects[runno] = thread
        thread.start()
        return runno

    def get_status_message(self, type, runno):
        if runno in self.thread_objects:
            status = self.thread_objects[runno].status()
            if status == "finished":
                self.save_dirnames_to_json()
            return status
        else:
            return 'Not Started'

    def create_random_directory_name(self, runno):
        dirname = 'test/'+str(uuid.uuid4())
        while dirname in self.dirnames.values():
            dirname = 'test/'+str(uuid.uuid4())
        self.dirnames[runno] = dirname
        return dirname

    def save_dirnames_to_json(self):
        with open('zmq_dirnames.json', 'w') as f:
            json.dump(self.dirnames, f)

    def load_dirnames_from_json(self):
        if os.path.isfile('zmq_dirnames.json'):
            with open('zmq_dirnames.json', 'r') as f:
                return  {int(k):v for k,v in json.load(f).items()}
        else:
            return {}

if __name__ == "__main__":
    server = zmqServer()
    server.run()
    while True:
        time.sleep(1)
