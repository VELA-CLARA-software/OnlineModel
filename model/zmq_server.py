import os, sys
import time
import zmq
import threading
import server_model as model
import logging
import uuid
from copy import deepcopy

sys.path.append(os.path.abspath(__file__+'/../../'))
import controller.run_parameters_parser as yaml_parser
import database.database_controller as dbc
import twissData as twissData

format = "%(asctime)s: %(message)s"
logging.basicConfig(format=format, level=logging.INFO,
                    datefmt="%H:%M:%S")

class Data(object):
    """Data object for running on the server."""
    def __init__(self):
        super(Data, self).__init__()

    def __getitem__(self, key):
        return getattr(self, key)

class modelThread(threading.Thread):
    """Thread object for running server model."""

    def __init__(self, datadict, runno, directoryname, dbcontroller, is_in_database=False):
        super(modelThread, self).__init__()
        self.runno = runno
        self.directoryname = 'test/'+directoryname
        self.datadict = datadict
        self.is_in_database = is_in_database
        self.data = Data()
        for k,v in datadict.items():
            # print(k,v)
            if isinstance(v,dict):
                setattr(self.data,k,v.copy())
            else:
                setattr(self.data,k,v)
        if not is_in_database:
            print('passing new run directory ', directoryname)
            self.track_model = model.Model(directoryname=self.directoryname, data=self.data, dbcontroller=dbcontroller, runno=self.runno)

    def run(self):
        """Run the model."""
        if not self.is_in_database:
            logging.info("Tracking Thread %s: starting", self.runno)
            self.track_model.run_script()
            self.data = self.track_model.data
            logging.info("Tracking Thread %s: finishing", self.runno)
        else:
            pass

    def get_status(self):
        """Return ifthe model is finished, or if not, progress in percent."""
        if self.is_in_database:
            return "finished"
        else:
            return self.track_model.Framework.progress if self.track_model.Framework.progress < 100 else "finished"

class twissThread(threading.Thread):
    """Thread object for reading and plotting output files."""

    def __init__(self, directory):
        super(twissThread, self).__init__()
        self.directory = directory
        self.twiss_model = twissData.twissData(directory='test/'+directory, name=directory)
        self.status = "Running"

    def run(self):
        """Run the plotting functions."""
        logging.info("Twiss Thread %s: starting", self.directory)
        # self.status = "\ttracking..."
        # self.twiss_model.run_script()
        self.twissData = self.twiss_model.run_script()
        self.status = self.twissData
        logging.info("Twiss Thread %s: finishing", self.directory)
        self.status = "Finished"

    def get_status(self):
        """Return the status of the thread, either Running or Finished."""
        return self.status

class zmqServer():
    """ZeroMQ instance to manage server interactions."""

    def __init__(self, port=8192):
        super(zmqServer, self).__init__()
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.port = port
        self.status = ""
        self.track_thread_objects = {}
        self.twiss_thread_objects = {}
        self.run_number = 0
        self.dbcontroller = dbc.DatabaseController()

    def get_next_runno(self):
        """Iterate the run number and return the new value."""
        runno = self.run_number
        self.run_number += 1
        return runno

    def poll_socket(self, socket, timetick = 100):
        """Poll the ZeroMQ socker yield a python object when interrupt occurs."""
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
        """Run the ZeroMQ socket poller."""
        print('Server starting on port:', self.port)
        self.socket.bind("tcp://*:%s" % (self.port))
        for message in self.poll_socket(self.socket):
            if isinstance(message, (list, tuple)):
                self.analyse_message(*message)
            else:
                self.analyse_message(message, [])

    def analyse_message(self, type, *args):
        """Analyse the received python object and call the required method."""
        if isinstance(type,str) and hasattr(self,type) and callable(getattr(self, type)):
            self.socket.send_pyobj(getattr(self, type)(*args))
        elif type == 'hello':
            self.socket.send_pyobj("hello from the server")
        else:
            self.socket.send_pyobj('Tick')

    def import_parameter_values_from_yaml_file(self, filename):
        """Import parameters from a YAML file."""
        filename = filename[0] if isinstance(filename,tuple) else filename
        filename = str(filename)
        if not filename == '' and not filename is None and (filename[-4:].lower() == '.yml' or filename[-5:].lower() == '.yaml'):
            # print('yaml filename = ', filename)
            loaded_parameter_dict = yaml_parser.parse_parameter_input_file(filename)
            # print('yaml data = ', loaded_parameter_dict)
            return loaded_parameter_dict
        else:
            return {}

    def get_absolute_folder_location(self, directoryname):
        """Return the current folder location."""
        return os.path.abspath(__file__+'/../../test/'+directoryname)

    def import_yaml(self, directoryname):
        """Import YAML file from a directory."""
        return self.import_parameter_values_from_yaml_file('test/'+directoryname+'/settings.yaml')

    def get_all_directory_names(self, *args):
        """Return all directory names."""
        return list(self.dbcontroller.get_all_run_ids())#{k:os.path.abspath(v) for k,v in self.dirnames.items()}

    def do_tracking_run(self, datadict):
        """Execute a tracking run using a thread."""
        runno = self.get_next_runno()
        yaml = model.create_yaml_dictionary(datadict)
        # del yaml['simulation']['directory']
        if self.are_settings_in_database(yaml):
            directoryname = self.get_run_id_for_settings(yaml)
        else:
            directoryname = self.create_random_directory_name()
        thread = modelThread(datadict, runno, directoryname, self.dbcontroller, is_in_database=self.are_settings_in_database(yaml))
        self.track_thread_objects[directoryname] = thread
        thread.start()
        return directoryname

    def get_tracking_status(self, directoryname):
        """Return the status of a tracking run based on the directory name."""
        if directoryname in self.track_thread_objects:
            status = self.track_thread_objects[directoryname].get_status()
            if status == "finished":
                yaml = model.create_yaml_dictionary(self.track_thread_objects[directoryname].data)
                self.save_settings_to_database(yaml, directoryname)
                del self.track_thread_objects[directoryname]
            return status
        else:
            return 'Not Started'

    def are_settings_in_database(self, yaml):
        """Check if the settings in a yaml dictionary are in the DB."""
        return self.dbcontroller.are_settings_in_database(yaml)

    def get_run_id_for_settings(self, yaml):
        """Return the run ID for a YAML dictionary in the DB."""
        if self.are_settings_in_database(yaml):
            return self.dbcontroller.get_run_id_for_settings(yaml)
        else:
            return None

    def do_twiss_run(self, directoryname):
        """Execute a twiss plotting routine using a thread."""
        # print('TWISS runno = ', runno)
        thread = twissThread(directoryname)
        self.twiss_thread_objects[directoryname] = thread
        thread.start()
        return directoryname

    def get_twiss_status(self, directoryname):
        """Return the status of a twiss plotting routine."""
        if directoryname in self.twiss_thread_objects:
            status = self.twiss_thread_objects[directoryname].get_status()
            if not status == "Running":
                data = self.twiss_thread_objects[directoryname].twissData
                # del self.twiss_thread_objects[runno]
            return status
        else:
            return 'Not Started'

    def create_random_directory_name(self):
        """Return a random UUID directory name."""
        dirname = str(uuid.uuid4())
        # while dirname in self.dirnames.values():
        #     dirname = 'test/'+str(uuid.uuid4())
        return dirname

    def save_settings_to_database(self, yaml, directoryname):
        """Save settings in a YAML dictionary to the DB."""
        self.dbcontroller.save_settings_to_database(yaml, directoryname)

if __name__ == "__main__":
    server = zmqServer()
    server.run()
    # while True:
    #     time.sleep(1)
