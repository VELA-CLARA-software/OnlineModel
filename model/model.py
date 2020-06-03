import os
import sys
import time
import stat
import zmq
import json

sys.path.append(os.path.join(str(os.path.dirname(os.path.abspath(__file__))), 'data'))
from data import data


class Model(object):
    def __init__(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.REQ)
        print('Connecting to server!')
        self.socket.connect("tcp://apclara2.dl.ac.uk:8192")
        print('sending hello!')
        self.socket.send_pyobj('hello')
        print('waiting for response!')
        response = self.socket.recv_pyobj()
        print('response = ', response)
        self.data = data.Data()
        self.progress = 0

    def run_script(self):
        data_dict = {'type': 'data dictionary'}
        data_dict['parameterDict'] = self.data.parameterDict
        data_dict['generatorDict'] = self.data.generatorDict
        data_dict['simulationDict'] = self.data.simulationDict
        data_dict['scanDict'] = self.data.scanDict
        data_dict['lattices'] = self.data.lattices
        # print('self.data.parameterDict = ', json.dumps(self.data.parameterDict))
        self.socket.send_pyobj(data_dict)
        response = run_number = self.socket.recv_pyobj()
        print(response)
        while not response == 'finished':
            response = self.socket.send_pyobj(['status', run_number])
            response = self.socket.recv_pyobj()
            self.progress = response
            print('Progress: ', self.progress, '%')
            time.sleep(1)
        return True

if __name__ == "__main__":
    model = Model()
