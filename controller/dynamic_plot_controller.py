from PyQt4.QtCore import *
from PyQt4.QtGui import *
from copy import copy,deepcopy
from decimal import Decimal
import run_parameters_parser as yaml_parser
import sys, os
sys.path.append(os.path.abspath(__file__+'/../../../OnlineModel/'))
from SimulationFramework.Modules.online_model_plotter import astraPlotWidget

class GenericThread(QThread):
    signal = pyqtSignal()

    def __init__(self, function, *args, **kwargs):
        QThread.__init__(self)
        self._stopped = False
        self.existent = 'existent file'
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def __del__(self):
        self.wait()

    def stop(self):
        self._stopped = True

    def run(self):
        self.signal.emit()
        if not self._stopped:
            self.object = self.function(*self.args, **self.kwargs)

class DynamicPlotController(QObject):

    def __init__(self, app, view, model):
        super(DynamicPlotController, self).__init__()
        self.my_name = 'controller'
        self.app = app
        self.model = model
        self.view = view
        self.view.main_tab_widget.removeTab(2)
        self.astraPlot = astraPlotWidget('./directory_summary_line_edit/')
        self.view.post_tab = self.astraPlot
        self.view.main_tab_widget.addTab(self.astraPlot, "Plots")
