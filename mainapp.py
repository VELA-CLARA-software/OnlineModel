"""Online Model v1.5.3."""
import sys
import argparse
import zmq
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtTest import QTest
from controller import (unified_controller, run_parameter_controller,
                        dynamic_plot_controller, database_controller)
from view import view
from model import remote_model as rmodel
from model import local_model as lmodel
QApplication.setAttribute(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

class MainApp(QObject):
    """Online Model main application."""

    def __init__(self, app, sys_argv=None):
        """Create the main application:
              - Initialise the view
              - Connect to the zeroMQ server if available
              - Initialise the DBC (DataBase Controller)
              - Initialise the local/remote model
              - Instantiate the RPC (Run Parameter Controller)
              - Instantiate the DPC (Dynamic Plot Controller)
              - Instantiate the Unified Controller passing in the RPC, the DPC and the DBC
              - Load settings file if required
        """
        super().__init__()
        parser = argparse.ArgumentParser(description='Add Sets.')
        parser.add_argument('-s', '--server', default=None, type=str)
        parser.add_argument('-p', '--port', default='8192', type=str)
        parser.add_argument('-f', '--config', default=None, type=str)
        parser.add_argument('-d', '--database', default=None, type=str)
        global args
        args = parser.parse_args(sys_argv)

        self.app = app
        self.view = view.Ui_MainWindow()
        use_server = self.initialise_zeromq()

        if ('args' in globals() or 'args' in locals()) and args.database is not None:
            self.database_controller = database_controller.DatabaseController(args.database)
        else:
            self.database_controller = database_controller.DatabaseController()
        if use_server is not False:
            print('Using REMOTE Model')
            self.model = rmodel.Model(self.socket)
        else:
            print('Using LOCAL Model')
            self.model = lmodel.Model()
            self.model.dbcontroller = self.database_controller
        self.MainWindow = QMainWindow()
        self.view.setupUi(self.MainWindow)
        self.RunParameterController = run_parameter_controller.RunParameterController(app, self.view, self.model)
        self.DynamicPlotController = dynamic_plot_controller.DynamicPlotController(app, self.view, self.model)
        # self.database_controller = database_controller.database_controller(self.socket)
        #self.PostProcessingController = post_processing_controller.PostProcessingController(app, self.view, self.model)
        self.UnifiedController = unified_controller.UnifiedController(self.RunParameterController, self.DynamicPlotController, self.database_controller)

        if ('args' in globals() or 'args' in locals()) and args.database is not None:
            self.UnifiedController.change_database_folder(args.database)
        else:
            self.UnifiedController.change_database_folder(self.database_controller.database)

        if ('args' in globals() or 'args' in locals()) and args.config is not None:
            self.import_yaml(args.config)

    def show(self):
        """Show the main window."""
        self.MainWindow.show()

    def initialise_zeromq(self):
        """Initialise the zeroMQ socket if using remote models."""
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
        return False

    def zmq_timeout_pyobj(self):
        """If zeroMQ server is not available return False, else return the server response."""
        poller = zmq.Poller()
        poller.register(self.socket, zmq.POLLIN)
        if poller.poll(1*1000): # 1s timeout in milliseconds
            response = self.socket.recv_pyobj()
            return response
        return False

    def modify_widget(self, aname, value):
        """Modify a GUI widgets value."""
        self.RunParameterController.update_widgets_with_values(aname, value)

    def get_widget_value(self, aname):
        """Return a GUI widgets value."""
        return self.RunParameterController.get_widget_value(self.RunParameterController.get_object_by_accessible_name(aname))

    def list_widget_layouts(self):
        """List all GUI widget layouts that are modifiable."""
        return self.RunParameterController.runParameterLayouts

    def list_widgets(self):
        """List all GUI widgets by their accessibleNames."""
        return [w for w in self.RunParameterController.accessibleNames.keys() if not w == '']

    def list_run_ids(self):
        """List all run IDs in the current DB."""
        return self.RunParameterController.model.get_all_directory_names()

    def plot_run_id(self, run_id):
        """Initiate a plot signal for the specified run ID."""
        self.RunParameterController.enable_plot_on_id(run_id)

    def plot_row(self, row):
        """Initiate a plot signal for a specified row in the run table."""
        self.RunParameterController.enable_plot_on_row(row)

    def clear_all_plots(self):
        """Initiate a clear plots signal."""
        self.RunParameterController.clear_all_plots()

    def get_id_for_row(self, row):
        """Get the run ID for a row in the run table."""
        return self.RunParameterController.get_id_for_row(row)

    def track(self):
        """Initiate a tracking run for the current settings."""
        self.view.runButton.clicked.emit()
        while not self.view.runButton.isEnabled():
            QTest.qWait(10)
        return self.get_widget_value('runs:directory')

    def set_plot_on_track(self, checked=True):
        """Toggle the state of the plot-on-track checkbox."""
        self.view.autoPlotCheckbox.setCheckState(checked)

    def get_screen_indices(self):
        """Return the current screens and their values."""
        combobox = self.DynamicPlotController.ompbeam.fileSelector
        return [[i, combobox.itemData(i)[0]] for i in range(combobox.count())]

    def set_screen_index(self, index):
        """Set the plot screen index to a specific value."""
        combobox = self.DynamicPlotController.ompbeam.fileSelector
        combobox.setCurrentIndex(index)

    def set_screen_name(self, screen):
        """Set the plot screen index to a specific screen name."""
        combobox = self.DynamicPlotController.ompbeam.fileSelector
        indices = list(zip(*self.get_screen_indices()))[1]
        combobox.setCurrentIndex(indices.index(screen))

    def get_twiss_at_screen_for_id(self, run_id):
        """Return the twiss values for the given run ID at the currently selected screen."""
        ompbeam = self.DynamicPlotController.ompbeam
        zpos = ompbeam.fileSelector.currentData()[1]
        return self.get_twiss_at_zpos_for_id(run_id, zpos)

    def get_twiss_at_zpos_for_id(self, run_id, zpos):
        """Return the twiss values at a specific zpos for a given run ID."""
        self.plot_run_id(run_id)
        ompbeam = self.DynamicPlotController.ompbeam
        twiss_data = ompbeam.globalTwissPlotWidget.twissDataObjects[run_id]
        twiss_values = {}
        for _, twiss in enumerate(ompbeam.twissFunctions):
            if not twiss[0] == 'run_id':
                twiss_values[twiss[0]] = twiss_data.get_parameter_at_z(twiss[0], zpos)
        return twiss_values

    def get_twiss_at_zpos_for_row(self, row, zpos):
        """Return the twiss values at a specific zpos for the given row in the run table."""
        self.plot_row(row)
        run_id = self.get_id_for_row(row)
        return self.get_twiss_at_zpos_for_id(run_id, zpos)

    def get_twiss_at_screen_for_row(self, row):
        """Return the twiss values for the given row in the run table at the currently selected screen."""
        self.plot_row(row)
        run_id = self.get_id_for_row(row)
        return self.get_twiss_at_screen_for_id(run_id)

    def get_twiss(self):
        """return the twiss values at the selected screen for all currently plotted run IDs."""
        ompbeam = self.DynamicPlotController.ompbeam
        zpos = ompbeam.fileSelector.currentData()[1]
        return self.get_twiss_at_zpos(zpos)

    def get_twiss_at_zpos(self, zpos):
        """return the twiss values at a specific zpos for all currently plotted run IDs."""
        ompbeam = self.DynamicPlotController.ompbeam
        twiss_values = {}
        for run_id in ompbeam.globalTwissPlotWidget.twissDataObjects:
            twiss_data = ompbeam.globalTwissPlotWidget.twissDataObjects[run_id]
            twiss_values[run_id] = {}
            for _, twiss in enumerate(ompbeam.twissFunctions):
                if not twiss[0] == 'run_id':
                    twiss_values[run_id][twiss[0]] = twiss_data.get_parameter_at_z(twiss[0], zpos)
        return twiss_values

    def get_twiss_object_for_row(self, row):
        """Return the twiss object for the specified row."""
        run_id = self.get_id_for_row(row)
        return self.get_twiss_object_for_id(run_id)

    def get_twiss_object_for_id(self, run_id):
        """Return the twiss object for the specified run ID."""
        self.plot_run_id(run_id)
        run_id = self.DynamicPlotController.basedirectoryname+'/'+run_id
        twiss_widget = self.DynamicPlotController.ompbeam.latticeTwissPlotWidget
        i = 0
        while not run_id in twiss_widget.twissDataObjects and i < 10:
            QTest.qWait(100)
            i += 1
        return twiss_widget.twissDataObjects[run_id]

    def get_slice_data(self):
        """Return the slice data for all currently plotted run IDs."""
        slice_data = {}
        slice_widget = self.DynamicPlotController.ompbeam.slicePlotWidget
        for run_id in slice_widget.curves.keys():
            slice_data[run_id] = self.get_slice_data_for_id(run_id)
        return slice_data

    def get_slice_data_for_row(self, row):
        """Return the slice data for the specified row."""
        run_id = self.get_id_for_row(row)
        return self.get_slice_data_for_id(run_id)

    def get_slice_data_for_id(self, run_id):
        """Return the slice data for the specified run ID."""
        self.plot_run_id(run_id)
        run_id = self.DynamicPlotController.basedirectoryname+'/'+run_id
        slice_data = {}
        slice_widget = self.DynamicPlotController.ompbeam.slicePlotWidget
        i = 0
        while not run_id in slice_widget.beams and i < 10:
            QTest.qWait(100)
            i += 1
            print(slice_widget.beams)
        allplotdataitems = slice_widget.curves[run_id]
        for var, plotdataitem in allplotdataitems.items():
            slice_data['t'] = plotdataitem.xData
            slice_data[var] = plotdataitem.yData
        return slice_data

    def get_beam_data(self):
        """Return the beam data for all currently plotted run IDs."""
        beam_data = {}
        beam_widget = self.DynamicPlotController.ompbeam.beamPlotWidget
        for run_id in beam_widget.curves.keys():
            beam_data[run_id] = self.get_beam_data_for_id(run_id)
        return beam_data

    def get_beam_data_for_row(self, row):
        """Return the beam data for the specified row."""
        run_id = self.get_id_for_row(row)
        return self.get_beam_data_for_id(run_id)

    def get_beam_data_for_id(self, run_id):
        """Return the beam data for the specified run ID."""
        self.plot_run_id(run_id)
        run_id = self.DynamicPlotController.basedirectoryname+'/'+run_id
        beam_data = {}
        beam_widget = self.DynamicPlotController.ompbeam.beamPlotWidget
        plotdataitem = beam_widget.curves[run_id]
        xvar = beam_widget.get_horizontal_variable()
        yvar = beam_widget.get_vertical_variable()
        beam_data[xvar['quantity']] = plotdataitem.xData
        beam_data[yvar['quantity']] = plotdataitem.yData
        return beam_data

    def get_beam_objects(self):
        """Return beam objects for all currently plotted run IDs."""
        return self.DynamicPlotController.ompbeam.beamPlotWidget.beams

    def get_beam_object_for_row(self, row):
        """Return the beam object for the specified row."""
        run_id = self.get_id_for_row(row)
        return self.get_beam_object_for_id(run_id)

    def get_beam_object_for_id(self, run_id):
        """Return the beam object for the specified run ID."""
        self.plot_run_id(run_id)
        run_id = self.DynamicPlotController.basedirectoryname+'/'+run_id
        beam_widget = self.DynamicPlotController.ompbeam.beamPlotWidget
        return beam_widget.beams[run_id]

    def export_yaml(self, *args, **kwargs):
        """Export a YAML file of the current settings."""
        self.RunParameterController.export_parameter_values_to_yaml_file(*args, **kwargs)

    def import_yaml(self, *args, **kwargs):
        """Import a YAML file of saved settings."""
        self.RunParameterController.import_parameter_values_from_yaml_file(*args, **kwargs)

    def set_database_file(self, database):
        """Change the database file."""
        self.database_controller = database_controller.database_controller(database)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app_object = MainApp(app)
    app_object.show()
    sys.exit(app.exec_())
