import sys
import os
import zmq
try:
    from PyQt4.QtCore import *
    from PyQt4.QtGui import *
except:
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *

sys.path.append(os.path.join(str(os.path.dirname(os.path.abspath(__file__))), 'model'))
sys.path.append(os.path.join(str(os.path.dirname(os.path.abspath(__file__))), 'controller'))
sys.path.append(os.path.join(str(os.path.dirname(os.path.abspath(__file__))), 'view'))
sys.path.append(os.path.join(str(os.path.dirname(os.path.abspath(__file__))), 'database'))

from controller import unified_controller, run_parameter_controller, post_processing_controller, dynamic_plot_controller
from view import view
from model import remote_model as rmodel
from model import local_model as lmodel
from database import database_controller
import argparse

parser = argparse.ArgumentParser(description='Add Sets.')
parser.add_argument('-s', '--server', default='apclara2.dl.ac.uk', type=str)
parser.add_argument('-p', '--port', default='8192', type=str)
args = parser.parse_args()

class MainApp(QObject):

    def __init__(self, app, sys_argv):

        super(MainApp, self).__init__()
        self.app = app
        self.view = view.Ui_MainWindow()
        use_server = self.initialise_zeromq()
        if use_server is not False:
            print('Using REMOTE Model')
            self.model = rmodel.Model(self.socket)
        else:
            print('Using LOCAL Model')
            self.model = lmodel.Model()
        self.MainWindow = QMainWindow()
        self.view.setupUi(self.MainWindow)
        self.RunParameterController = run_parameter_controller.RunParameterController(app, self.view, self.model)
        self.DynamicPlotController = dynamic_plot_controller.DynamicPlotController(app, self.view, self.model)
        # self.DatabaseController = database_controller.DatabaseController(self.socket)
        #self.PostProcessingController = post_processing_controller.PostProcessingController(app, self.view, self.model)
        self.UnifiedController = unified_controller.UnifiedController(self.RunParameterController, self.DynamicPlotController)
        #                                                              self.PostProcessingController)
        self.MainWindow.show()

    def initialise_zeromq(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.REQ)
        self.socket.setsockopt(zmq.LINGER, 1)
        print('Connecting to server at ',args.server,':',args.port)
        self.socket.connect("tcp://"+args.server+":"+args.port+"")
        print('sending hello!')
        self.socket.send_pyobj('hello')
        print('waiting for response!')
        print(self.zmq_timeout_pyobj())
            # raise IOError("Timeout processing auth request")

    def zmq_timeout_pyobj(self):
        poller = zmq.Poller()
        poller.register(self.socket, zmq.POLLIN)
        if poller.poll(1*1000): # 1s timeout in milliseconds
            response = self.socket.recv_pyobj()
            return response
        else:
            return False

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app_object = MainApp(app, sys.argv)
    sys.exit(app.exec_())
