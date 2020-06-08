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

sys.path.append(os.path.abspath(__file__+'/../../'))
import controller.run_parameters_parser as yaml_parser

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
        print('passing new run directory ', directoryname)
        self.track_model = model.Model(directoryname=self.directoryname, data=self.data, runno=self.runno)
        # self.status = ""

    def run(self):
        logging.info("Tracking Thread %s: starting", self.runno)
        # self.status = "\ttracking..."
        self.track_model.run_script()
        logging.info("Tracking Thread %s: finishing", self.runno)
        # self.status = "finished"

    def get_status(self):
        return self.track_model.Framework.progress if self.track_model.Framework.progress < 100 else "finished"

class twissThread(threading.Thread):

    def __init__(self, directory, runno):
        super(twissThread, self).__init__()
        self.runno = runno
        self.twiss_model = model.twissData(directory=directory, name=runno)
        self.status = "Running"

    def run(self):
        logging.info("Twiss Thread %s: starting", self.runno)
        # self.status = "\ttracking..."
        self.twiss_model.run_script()
        self.twissData = self.twiss_model.run_script()
        self.status = self.twissData
        logging.info("Twiss Thread %s: finishing", self.runno)

    def get_status(self):
        return self.status

class zmqServer():

    def __init__(self, port=8192):
        super(zmqServer, self).__init__()
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.port = port
        self.status = ""
        self.track_thread_objects = {}
        self.twiss_thread_objects = {}
        self.dirnames = self.load_dirnames_from_json()
        print(self.dirnames)

    def get_next_runno(self):
        return next(i for i, e in enumerate(sorted(self.dirnames.keys()) + [ None ], 1) if i != e)

    def poll_socket(self, socket, timetick = 100):
        poller = zmq.Poller()
        poller.register(socket, zmq.POLLIN)
        # wait up to 100msec
        try:
            while True:
                obj = dict(poller.poll(timetick))
                if socket in obj and obj[socket] == zmq.POLLIN:
                    yield socket.recv_pyobj()
        except KeyboardInterrupt:
            pass
        # Escape while loop if there's a keyboard interrupt.

    def run(self):
        print('Server starting on port:', self.port)
        self.socket.bind("tcp://*:%s" % (self.port))
        for message in self.poll_socket(self.socket):
            if isinstance(message, (list, tuple)):
                self.analyse_message(*message)
            else:
                self.analyse_message(message, [])

    def analyse_message(self, type, *args):
        if isinstance(type,str) and hasattr(self,type) and callable(getattr(self, type)):
            self.socket.send_pyobj(getattr(self, type)(*args))
        elif type == 'hello':
            self.socket.send_pyobj("hello from the server")
        else:
            self.socket.send_pyobj('Tick')

    def export_yaml(self, runno):
        if runno in self.dirnames.keys():
            return 'YAML exported to '+str(self.dirnames[runno])
        else:
            return 'YAML not exported - key not found'

    def import_parameter_values_from_yaml_file(self, filename):
        filename = filename[0] if isinstance(filename,tuple) else filename
        filename = str(filename)
        if not filename == '' and not filename is None and (filename[-4:].lower() == '.yml' or filename[-5:].lower() == '.yaml'):
            # print('yaml filename = ', filename)
            loaded_parameter_dict = yaml_parser.parse_parameter_input_file(filename)
            # print('yaml data = ', loaded_parameter_dict)
            return loaded_parameter_dict
        else:
            return {}

    def import_yaml(self, runno):
        runno = int(runno)
        if runno in self.dirnames.keys():
            return self.import_parameter_values_from_yaml_file(self.dirnames[runno]+'/settings.yaml')

    def get_directory_name(self, runno):
        if runno in self.dirnames.keys():
            return os.path.abspath(self.dirnames[runno])
        else:
            return 'Directory Name not returned - key not found'

    def get_all_directory_names(self, *args):
        return {k:os.path.abspath(v) for k,v in self.dirnames.items()}

    def do_tracking_run(self, datadict):
        runno = self.get_next_runno()
        print('runno = ', runno)
        directoryname = self.create_random_directory_name(runno)
        thread = modelThread(datadict, runno, directoryname)
        self.track_thread_objects[runno] = thread
        thread.start()
        return runno

    def get_tracking_status(self, runno):
        if runno in self.track_thread_objects:
            status = self.track_thread_objects[runno].get_status()
            if status == "finished":
                self.save_dirnames_to_json()
                del self.track_thread_objects[runno]
            return status
        else:
            return 'Not Started'

    def do_twiss_run(self, runno):
        # print('TWISS runno = ', runno)
        directoryname = self.dirnames[int(runno)]
        thread = twissThread(directoryname, runno)
        self.twiss_thread_objects[runno] = thread
        thread.start()
        return runno

    def get_twiss_status(self, runno):
        if runno in self.twiss_thread_objects:
            status = self.twiss_thread_objects[runno].get_status()
            if not status == "Running":
                data = self.twiss_thread_objects[runno].twissData
                # del self.twiss_thread_objects[runno]
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
                return  {int(k):v for k,v in json.load(f).items() if os.path.isdir(v)}
        else:
            return {}

if __name__ == "__main__":
    server = zmqServer()
    server.run()
    # while True:
    #     time.sleep(1)
