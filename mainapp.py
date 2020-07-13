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
from model import model
from database import database_controller

class MainApp(QObject):

    def __init__(self, app, sys_argv):

        super(MainApp, self).__init__()
        self.app = app
        self.view = view.Ui_MainWindow()
        self.initialise_zeromq()
        self.model = model.Model(self.socket)
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
        print('Connecting to server!')
        # self.socket.connect("tcp://apclara2.dl.ac.uk:8192")
        self.socket.connect("tcp://localhost:8192")
        print('sending hello!')
        self.socket.send_pyobj('hello')
        print('waiting for response!')
        response = self.socket.recv_pyobj()
        print('response = ', response)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app_object = MainApp(app, sys.argv)
    sys.exit(app.exec_())
