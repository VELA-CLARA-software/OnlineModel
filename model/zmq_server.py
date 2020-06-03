import os, sys
import time
import zmq
import threading
import signal
import server_model as model
import logging
from copy import deepcopy

format = "%(asctime)s: %(message)s"
logging.basicConfig(format=format, level=logging.INFO,
                    datefmt="%H:%M:%S")

class Data(object):

    def __init__(self):
        super(Data, self).__init__()

class modelThread(threading.Thread):

    def __init__(self, msg, runno):
        super(modelThread, self).__init__()
        self.data = Data()
        for k,v in msg.items():
            if isinstance(v,dict):
                setattr(self.data,k,v.copy())
            else:
                setattr(self.data,k,v)
        self.runno = runno
        self.track_model = model.Model(data=self.data, runno=self.runno)
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
        self.runs = 0
        self.thread_objects = {}

    def run(self):
        print('Server starting on port:', self.port)
        self.socket.bind("tcp://*:%s" % (self.port))
        while True:
            msg = self.socket.recv_pyobj()
            if isinstance(msg, dict) and msg['type'] == 'data dictionary':
                self.runs += 1
                thread = modelThread(msg, self.runs)
                self.thread_objects[self.runs] = thread
                thread.start()
                self.socket.send_pyobj(self.runs)
            elif isinstance(msg, list) and msg[0] == 'status':
                if msg[1] in self.thread_objects:
                    self.socket.send_pyobj(self.thread_objects[msg[1]].status())
            elif msg == 'hello':
                self.socket.send_pyobj("hello from the server")

if __name__ == "__main__":
    server = zmqServer()
    server.run()
    while True:
        time.sleep(1)
