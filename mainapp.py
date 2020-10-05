import sys
import time
import os
import zmq
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtTest import *
from pyqtgraph import DataTreeWidget
QApplication.setAttribute(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
sys.path.append(os.path.join(str(os.path.dirname(os.path.abspath(__file__))), 'model'))
sys.path.append(os.path.join(str(os.path.dirname(os.path.abspath(__file__))), 'controller'))
sys.path.append(os.path.join(str(os.path.dirname(os.path.abspath(__file__))), 'view'))
sys.path.append(os.path.join(str(os.path.dirname(os.path.abspath(__file__))), 'database'))

from controller import unified_controller, run_parameter_controller, dynamic_plot_controller, database_controller
from view import view
from model import remote_model as rmodel
from model import local_model as lmodel
from detachable_tab_widget import DetachableTabWidget
import argparse

class MainApp(QObject):

    def __init__(self, app, sys_argv):

        super(MainApp, self).__init__()
        self.app = app
        self.view = view.Ui_MainWindow()
        use_server = self.initialise_zeromq()

        if ('args' in globals() or 'args' in locals()) and args.database is not None:
            self.DatabaseController = database_controller.DatabaseController(args.database)
        else:
            self.DatabaseController = database_controller.DatabaseController()
        if use_server is not False:
            print('Using REMOTE Model')
            self.model = rmodel.Model(self.socket)
        else:
            print('Using LOCAL Model')
            self.model = lmodel.Model()
            self.model.dbcontroller = self.DatabaseController
        self.MainWindow = QMainWindow()
        self.view.setupUi(self.MainWindow)
        self.RunParameterController = run_parameter_controller.RunParameterController(app, self.view, self.model)
        self.DynamicPlotController = dynamic_plot_controller.DynamicPlotController(app, self.view, self.model)
        # self.DatabaseController = database_controller.DatabaseController(self.socket)
        #self.PostProcessingController = post_processing_controller.PostProcessingController(app, self.view, self.model)
        self.UnifiedController = unified_controller.UnifiedController(self.RunParameterController, self.DynamicPlotController, self.DatabaseController)

        if ('args' in globals() or 'args' in locals()) and args.config is not None:
            self.import_yaml(args.config)

    def show(self):
        self.MainWindow.show()

    def initialise_zeromq(self):
        if 'args' in globals():
            if args.server is not None:
                context = zmq.Context()
                self.socket = context.socket(zmq.REQ)
                self.socket.setsockopt(zmq.LINGER, 1)
                print('Connecting to server at ',args.server,':',args.port)
                self.socket.connect("tcp://"+args.server+":"+args.port+"")
                print('sending hello!')
                self.socket.send_pyobj('hello')
                print('waiting for response!')
                return self.zmq_timeout_pyobj()
            else:
                return False
        else:
            return False

    def zmq_timeout_pyobj(self):
        poller = zmq.Poller()
        poller.register(self.socket, zmq.POLLIN)
        if poller.poll(1*1000): # 1s timeout in milliseconds
            response = self.socket.recv_pyobj()
            return response
        else:
            return False

    def modify_widget(self, aname, value):
        self.RunParameterController.update_widgets_with_values(aname, value)

    def get_widget_value(self, aname):
        return self.RunParameterController.get_widget_value(self.RunParameterController.get_object_by_accessible_name(aname))

    def list_widget_layouts(self):
        return self.RunParameterController.runParameterLayouts

    def list_widgets(self):
        return [w for w in self.RunParameterController.accessibleNames.keys() if w is not '']

    def list_run_ids(self):
        return self.RunParameterController.model.get_all_directory_names()

    def plot_run_id(self, id):
        self.RunParameterController.enable_plot_on_id(id)

    def plot_row(self, row):
        self.RunParameterController.enable_plot_on_row(row)

    def clear_all_plots(self):
        self.RunParameterController.clear_all_plots()

    def get_id_for_row(self, row):
        return self.RunParameterController.get_id_for_row(row)

    def track(self):
        self.view.runButton.clicked.emit()
        while not self.view.runButton.isEnabled():
            QTest.qWait(10)
        # self.RunParameterController.enable_run_button()
        # self.RunParameterController.save_settings_to_database(self.view.autoPlotCheckbox.isChecked())
        # self.RunParameterController.update_directory_widget()
        return self.get_widget_value('runs:directory')

    def set_plot_on_track(self, checked=True):
        self.view.autoPlotCheckbox.setCheckState(checked)

    def get_screen_indices(self):
        combobox = self.DynamicPlotController.ompbeam.fileSelector
        return [[i, combobox.itemData(i)[0]] for i in range(combobox.count())]

    def set_screen_index(self, index):
        combobox = self.DynamicPlotController.ompbeam.fileSelector
        combobox.setCurrentIndex(index)

    def set_screen_name(self, screen):
        combobox = self.DynamicPlotController.ompbeam.fileSelector
        indices = list(zip(*self.get_screen_indices()))[1]
        combobox.setCurrentIndex(indices.index(screen))

    def get_twiss_at_screen_for_id(self, run_id):
        ompbeam = self.DynamicPlotController.ompbeam
        zpos = ompbeam.fileSelector.currentData()[1]
        return self.get_twiss_at_zpos_for_id(run_id, zpos)

    def get_twiss_at_zpos_for_id(self, run_id, zpos):
        self.plot_run_id(run_id)
        ompbeam = self.DynamicPlotController.ompbeam
        twissData = ompbeam.globalTwissPlotWidget.twissDataObjects[run_id]
        twissValues = {}
        for row, twiss in enumerate(ompbeam.twissFunctions):
            if not twiss[0] == 'run_id':
                twissValues[twiss[0]] = twissData.get_parameter_at_z(twiss[0], zpos)
        return twissValues

    def get_twiss_at_zpos_for_row(self, row, zpos):
        self.plot_row(row)
        id = self.get_id_for_row(row)
        return self.get_twiss_at_zpos_for_id(id, zpos)

    def get_twiss_at_screen_for_row(self, row):
        self.plot_row(row)
        id = self.get_id_for_row(row)
        return self.get_twiss_at_screen_for_id(id)

    def get_twiss(self):
        ompbeam = self.DynamicPlotController.ompbeam
        zpos = ompbeam.fileSelector.currentData()[1]
        return self.get_twiss_at_zpos(zpos)

    def get_twiss_at_zpos(self, zpos):
        ompbeam = self.DynamicPlotController.ompbeam
        twissValues = {}
        for run_id in ompbeam.globalTwissPlotWidget.twissDataObjects:
            twissData = ompbeam.globalTwissPlotWidget.twissDataObjects[run_id]
            twissValues[run_id] = {}
            for row, twiss in enumerate(ompbeam.twissFunctions):
                if not twiss[0] == 'run_id':
                    twissValues[run_id][twiss[0]] = twissData.get_parameter_at_z(twiss[0], zpos)
        return twissValues

    def get_twiss_object_for_row(self, row):
        id = self.get_id_for_row(row)
        return self.get_twiss_object_for_id(id)

    def get_twiss_object_for_id(self, id):
        self.plot_run_id(id)
        twissWidget = self.DynamicPlotController.ompbeam.latticeTwissPlotWidget
        i = 0
        while not id in twissWidget.twissDataObjects and i < 10:
            QTest.qWait(100)
            i += 1
        return twissWidget.twissDataObjects[id]

    def get_slice_data(self):
        slicedata = {}
        sliceWidget = self.DynamicPlotController.ompbeam.slicePlotWidget
        for id in sliceWidget.curves.keys():
            slicedata[id] = self.get_slice_data_for_id(id)
        return slicedata

    def get_slice_data_for_row(self, row):
        id = self.get_id_for_row(row)
        return self.get_slice_data_for_id(id)

    def get_slice_data_for_id(self, id):
        self.plot_run_id(id)
        slicedata = {}
        sliceWidget = self.DynamicPlotController.ompbeam.slicePlotWidget
        i = 0
        while not id in sliceWidget.beams and i < 10:
            QTest.qWait(100)
            i += 1
            print(sliceWidget.beams)
        allplotdataitems = sliceWidget.curves[id]
        for var, plotdataitem in allplotdataitems.items():
            slicedata['t'] = plotdataitem.xData
            slicedata[var] = plotdataitem.yData
        return slicedata

    def get_beam_data(self):
        beamdata = {}
        beamWidget = self.DynamicPlotController.ompbeam.beamPlotWidget
        for id in beamWidget.curves.keys():
            beamdata[id] = self.get_beam_data_for_id(id)
        return beamdata

    def get_beam_data_for_row(self, row):
        id = self.get_id_for_row(row)
        return self.get_beam_data_for_id(id)

    def get_beam_data_for_id(self, id):
        self.plot_run_id(id)
        beamdata = {}
        beamWidget = self.DynamicPlotController.ompbeam.beamPlotWidget
        plotdataitem = beamWidget.curves[id]
        xvar = beamWidget.get_horizontal_variable()
        yvar = beamWidget.get_vertical_variable()
        beamdata[xvar['quantity']] = plotdataitem.xData
        beamdata[yvar['quantity']] = plotdataitem.yData
        return beamdata

    def get_beam_objects(self):
        return self.DynamicPlotController.ompbeam.beamPlotWidget.beams

    def get_beam_object_for_row(self, row):
        id = self.get_id_for_row(row)
        return self.get_beam_object_for_id(id)

    def get_beam_object_for_id(self, id):
        self.plot_run_id(id)
        beamWidget = self.DynamicPlotController.ompbeam.beamPlotWidget
        return beamWidget.beams[id]

    def export_yaml(self, *args, **kwargs):
        self.RunParameterController.export_parameter_values_to_yaml_file(*args, **kwargs)

    def import_yaml(self, *args, **kwargs):
        self.RunParameterController.import_parameter_values_from_yaml_file(*args, **kwargs)

    def set_database_file(self, database):
        self.DatabaseController = database_controller.DatabaseController(database)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Add Sets.')
    parser.add_argument('-s', '--server', default=None, type=str)
    parser.add_argument('-p', '--port', default='8192', type=str)
    parser.add_argument('-f', '--config', default=None, type=str)
    parser.add_argument('-d', '--database', default=None, type=str)
    args = parser.parse_args()
    print(args)

    app = QApplication(sys.argv)
    app_object = MainApp(app, sys.argv)
    app_object.show()
    sys.exit(app.exec_())
