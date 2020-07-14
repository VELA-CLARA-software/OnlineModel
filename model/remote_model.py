import os
import sys
import time
import stat

sys.path.append(os.path.join(str(os.path.dirname(os.path.abspath(__file__))), 'data'))
from data import data

class Model(object):
    def __init__(self, socket):
        self.socket = socket
        self.data = data.Data()
        self.progress = 0
        self.run_number = -1
        self.yaml = None
        self.directoryname = None

    def run_script(self):
        data_dict = {}
        data_dict['parameterDict'] = self.data.parameterDict
        data_dict['generatorDict'] = self.data.generatorDict
        data_dict['simulationDict'] = self.data.simulationDict
        data_dict['scanDict'] = self.data.scanDict
        data_dict['lattices'] = self.data.lattices
        self.socket.send_pyobj(['do_tracking_run',data_dict])
        response = run_number = self.socket.recv_pyobj()
        self.directoryname = run_number
        print(response)
        while not response == 'finished':
            response = self.socket.send_pyobj(['get_tracking_status', run_number])
            response = self.socket.recv_pyobj()
            self.progress = response
            print('Progress: ', self.progress, '%')
            time.sleep(0.1)
        return True

    def get_directory_name(self):
        return self.directoryname

    def export_yaml_on_server(self):
        response = self.socket.send_pyobj(['export_yaml', self.directoryname])
        return self.socket.recv_pyobj()

    def import_yaml_from_server(self, runno=None):
        if runno is None:
            runno = self.directoryname
        response = self.socket.send_pyobj(['import_yaml', runno])
        return self.socket.recv_pyobj()

    def get_all_directory_names(self):
        response = self.socket.send_pyobj(['get_all_directory_names'])
        return self.socket.recv_pyobj()

    def run_twiss(self, id):
        self.socket.send_pyobj(['do_twiss_run',id])
        run_number = self.socket.recv_pyobj()
        response = self.socket.send_pyobj(['get_twiss_status', run_number])
        response = self.socket.recv_pyobj()
        while response == 'Running' or response == 'Not Started':
            response = self.socket.send_pyobj(['get_twiss_status', run_number])
            response = self.socket.recv_pyobj()
            time.sleep(0.01)
        return response

    def save_settings_to_database(self, *args, **kwargs):
        pass

if __name__ == "__main__":
    model = Model()
