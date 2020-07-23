import os
import sys
import time
import stat

sys.path.append(os.path.abspath(__file__+'/../../'))
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
        self.progress = 0
        data_dict = {}
        data_dict['parameterDict'] = self.data.parameterDict
        data_dict['generatorDict'] = self.data.generatorDict
        # data_dict['simulationDict'] = self.data.simulationDict
        data_dict['scanDict'] = self.data.scanDict
        data_dict['runsDict'] = self.data.runsDict
        data_dict['lattices'] = self.data.lattices
        self.socket.send_pyobj(['do_tracking_run', data_dict])
        response = run_number = self.socket.recv_pyobj()
        self.directoryname = run_number
        print(response)
        while not response == 'finished':
            response = self.socket.send_pyobj(['get_tracking_status', run_number])
            response = self.socket.recv_pyobj()
            progress = response
            if not progress == self.progress:
                print('Progress: ', self.progress, '%')
                self.progress = progress
            time.sleep(0.1)
        print('Progress: ', response)
        return True

    def get_directory_name(self):
        return self.directoryname

    def export_parameter_values_to_yaml_file(self, *args, **kwargs):
        pass

    def import_yaml(self, runno=None):
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

    def get_absolute_folder_location(self, dir):
        response = self.socket.send_pyobj(['get_absolute_folder_location', dir])
        return self.socket.recv_pyobj()

if __name__ == "__main__":
    model = Model()
