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
        print('Hello from the DynamicPlotController!')
        # del self.view.post_tab
        # self.view.remove
        self.view.main_tab_widget.removeTab(2)
        self.astraPlot = astraPlotWidget('./directory_summary_line_edit/')
        self.view.post_tab = self.astraPlot
        self.view.main_tab_widget.addTab(self.astraPlot, "Plots")
        # self.view.post_tab.show()
        print(self.view.post_tab)
        # exit()
        # #self.model.data.self.model.data.runParameterDict = self.initialize_run_parameter_data()
        # self.initialize_run_parameter_data()
        # self.model.data.scannableParametersDict = self.get_scannable_parameters_dict()
        # self.populate_scan_combo_box()
        # self.model.data.parameterScanDict = self.initialize_parameter_scan_data()
        # self.model.data.directoryDict = self.initialize_directory_data()
        # self.view.parameter_scan.stateChanged.connect(self.toggle_scan_parameters_state)
        # self.view.runButton.clicked.connect(self.run_astra)
