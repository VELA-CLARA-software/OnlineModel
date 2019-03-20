import sys
import os
from PyQt4.QtCore import *
from PyQt4.QtGui import *

sys.path.append(os.path.join(str(os.path.dirname(os.path.abspath(__file__))), 'model'))
sys.path.append(os.path.join(str(os.path.dirname(os.path.abspath(__file__))), 'controller'))
sys.path.append(os.path.join(str(os.path.dirname(os.path.abspath(__file__))), 'view'))

from controller import controller
from view import view
from model import model


class MainApp(QObject):

    def __init__(self, app, sys_argv):

        super(MainApp, self).__init__()
        self.app = app
        self.view = view.Ui_MainWindow()
        self.model = model.Model()
        self.model.username = 'qfi29231'
        self.model.password = "qd'3xk.mr6&&"
        self.MainWindow = QMainWindow()
        self.view.setupUi(self.MainWindow)
        self.controller = controller.Controller(app, self.view, self.model)
        self.MainWindow.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app_object = MainApp(app, sys.argv)
    sys.exit(app.exec_())
