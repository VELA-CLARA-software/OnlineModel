import sys
import os
from PyQt4.QtCore import *
from PyQt4.QtGui import *

sys.path.append(os.path.join(str(os.path.dirname(os.path.abspath(__file__))), 'model'))
sys.path.append(os.path.join(str(os.path.dirname(os.path.abspath(__file__))), 'controller'))
sys.path.append(os.path.join(str(os.path.dirname(os.path.abspath(__file__))), 'view'))

from controller import unified_controller, run_parameter_controller, post_processing_controller
from view import view
from model import model


class MainApp(QObject):

    def __init__(self, app, sys_argv):

        super(MainApp, self).__init__()
        self.app = app
        self.view = view.Ui_MainWindow()
        self.model = model.Model()
        self.model.username = 'DLERLP'
        self.model.password = "3r!pc0~1"
        self.MainWindow = QMainWindow()
        self.view.setupUi(self.MainWindow)
        self.RunParameterController = run_parameter_controller.RunParameterController(app, self.view, self.model)
        #self.PostProcessingController = post_processing_controller.PostProcessingController(app, self.view, self.model)
        self.UnifiedController = unified_controller.UnifiedController(self.RunParameterController)
        #                                                              self.PostProcessingController)
        self.MainWindow.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app_object = MainApp(app, sys.argv)
    sys.exit(app.exec_())
