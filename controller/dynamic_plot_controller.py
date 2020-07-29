try:
    from PyQt4.QtCore import *
    from PyQt4.QtGui import *
except:
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *
from copy import copy,deepcopy
from decimal import Decimal
import sys, os
sys.path.append(os.path.abspath(__file__+'/../../'))
sys.path.append(os.path.abspath(__file__+'/../../../OnlineModel/'))
sys.path.append(os.path.abspath(__file__+'/../../../SimFrame/'))
import database.run_parameters_parser as yaml_parser
from SimulationFramework.Modules.online_model_twissPlot import twissPlotWidget

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

    plotcolor = pyqtSignal(int, QColor)

    def __init__(self, app, view, model):
        super(DynamicPlotController, self).__init__()
        self.my_name = 'controller'
        self.app = app
        self.model = model
        self.view = view
        self.view.main_tab_widget.removeTab(3)
        self.omp = twissPlotWidget()
        # self.view.post_tab = self.omp
        self.view.main_tab_widget.addTab(self.omp, "Plots")

    def add_twiss_plot(self, id, dir):
        # dir = dir.replace('/mnt/','\\\\').replace('/','\\')+'\\'
        # print('adding twiss plot: ', dir)
        # self.omp.addTwissDirectory([{'directory': dir, 'sections': 'All'}], name=id)
        print('Requesting Twiss - ', dir)
        twissdata = self.model.run_twiss(dir)
        color, style = self.omp.addtwissDataObject(dataobject=twissdata, name=dir)
        self.plotcolor.emit(id, color)

    def remove_twiss_plot(self, dir):
        print('Removing twiss plot: ', dir)
        self.omp.removeCurve(dir)
