try:
    from PyQt4.QtCore import *
    from PyQt4.QtGui import *
except:
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *
from . import run_parameters_parser as yaml_parser
from model.local_model import create_yaml_dictionary, Model
import controller.run_table as run_table
from controller import database_controller
import sys, os, re
import time
import collections
import numpy as np
import pyqtgraph as pg
from copy import deepcopy
from deepdiff import DeepDiff

class CheckableComboBox(QComboBox):
    # once there is a checkState set, it is rendered
    # here we assume default Unchecked

    tagChanged = pyqtSignal()
    tagChecked = pyqtSignal(str)
    tagUnchecked = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super(CheckableComboBox, self).__init__()
        self.view().clicked.connect(self.addRemoveTags)

    def addCheckableItem(self, item):
        self.addItem(item)
        item = self.model().item(self.count()-1,0)
        item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        item.setCheckState(Qt.Unchecked)

    def itemChecked(self, index):
        item = self.model().item(index,0)
        return item.checkState() == Qt.Checked

    def addRemoveTags(self, index):
        tag = self.model().item(index.row(),0).text()
        if self.itemChecked(index.row()):
            self.tagChecked.emit(tag)
        else:
            self.tagUnchecked.emit(tag)
        self.tagChanged.emit()

    def setTagState(self, tag, state):
        if state == Qt.Unchecked or state == Qt.Checked:
            for i in range(self.count()):
                item = self.model().item(i-1,0)
                if item.text() == tag:
                    item.setCheckState(state)

    def setTagStates(self, checkedtags=[]):
        for i in range(self.count()):
            item = self.model().item(i-1,0)
            if item is not None:
                if item.text() in checkedtags:
                    item.setCheckState(Qt.Checked)
                else:
                    item.setCheckState(Qt.Unchecked)

    def getTagText(self, index):
        return self.model().item(index,0).text()

    def getCheckedTags(self, checkedtags=[]):
        return [self.getTagText(i) for i in range(self.count()) if self.itemChecked(i)]

class userWidget(QWidget):

    update = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(userWidget, self).__init__()

    def value(self):
        return os.getlogin()

class timeWidget(QWidget):

    update = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(timeWidget, self).__init__()

    def value(self):
        return time.time()

class GenericThread(QThread):
    signal = pyqtSignal()

    def __init__(self, function, *args, **kwargs):
        super(GenericThread, self).__init__()
        self._stopped = False
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

class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        `tuple` (exctype, value, traceback.format_exc() )

    result
        `object` data returned from processing, anything

    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)

class GenericWorker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(GenericWorker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            pass
        self.signals.finished.emit()  # Done

class signalling_monitor(QObject):

    valueChanged = pyqtSignal(int)

    def __init__(self, ref, parameter, interval=200):
        super(signalling_monitor, self).__init__()
        self.timer = QTimer(self)
        self.timer.setInterval(interval)
        self.timer.timeout.connect(self.emitValue)
        self.ref = ref
        self.parameter = parameter

    def stop(self):
        self.timer.stop()

    def start(self, interval=None):
        self.setInterval(interval)
        self.timer.start()

    def setInterval(self, interval):
        if interval is not None:
            self.timer.setInterval(interval)

    def emitValue(self):
        self.valueChanged.emit(getattr(self.ref, self.parameter))

class RunParameterController(QObject):

    add_plot_signal = pyqtSignal(int, str)
    remove_plot_signal = pyqtSignal(str)
    delete_run_id_signal = pyqtSignal(str)
    add_plot_window_signal = pyqtSignal(int, str)
    run_id_clicked_signal = pyqtSignal(str)
    change_database_signal = pyqtSignal(str)
    run_finished_signal = pyqtSignal(int, int, str, dict, int)

    tags = ['BA1', 'User Experiment', 'Front End', 'Emittance', 'Energy Spread', 'Commissioning']

    run_table_columns = {'run_id': 1, 'load_run_button': 0, 'plot_checkbox': 2, 'plot_color': 3, 'time_stamp':4}

    def __init__(self, app, view, model):
        super(RunParameterController, self).__init__()
        self.my_name = 'controller'
        self.app = app
        self.model = model
        self.view = view
        self.create_user_tag_combo_box()
        self.runParameterLayouts = [
                               self.view.s02_parameter_groupbox,
                               self.view.c2v_parameter_groupbox,
                               self.view.vela_parameter_groupbox,
                               self.view.ba1_parameter_groupbox,
                               self.view.injector_parameter_groupbox,
                               self.view.simulation_parameter_groupbox,
                               self.view.scan_groupBox,
                               self.view.directory_groupBox,
                               self.view.tags_widget,
                               self.view.laser_cal_widget,
                               ]
        self.formLayoutList = [formLayout for layout in self.runParameterLayouts for
                          formLayout in layout.findChildren((QFormLayout,QGridLayout))]
        self.accessibleNames = {}
        for layout in self.formLayoutList:
            childCount = layout.count()
            for child in range(0,childCount):
                widget = layout.itemAt(child).widget()
                if widget is not None and widget.accessibleName() is not None:
                    self.accessibleNames[widget.accessibleName()] = widget
                else:
                    pass
        self.update_macro_particle_combo()
        self.initialize_run_parameter_data()
        self.model.data.scannableParametersDict = self.get_scannable_parameters_dict()
        self.view.scan_tabWidget.scanTabAdded.connect(self.populate_scan_combo_box)
        self.view.scan_tabWidget.scanTabRemoved.connect(self.remove_scan_dict)
        self.view.scan_tabWidget.addScanTab()
        # self.populate_scan_combo_box(1)
        # self.view.parameter_scan.stateChanged.connect(lambda: self.toggle_scan_parameters_state(self.view.parameter_scan))
        self.view.bsol_track_checkBox.stateChanged.connect(self.toggle_BSOL_tracking)
        self.view.runButton.clicked.connect(self.app_sequence)
        self.view.directory.textChanged[str].emit(self.view.directory.text())
        self.view.clearPlotsButton.clicked.connect(self.clear_all_plots)
        self.run_finished_signal.connect(self.run_finished)
        self.abort_scan = False
        self.run_plots = []
        self.run_plot_colors = {}
        self.table_match = re.compile(r"\['([a-zA-Z\-0-9_]*)'\]")
        start = time.time()
        self.create_datatree_widget()
        self.populate_run_parameters_table()
        self.toggle_BSOL_tracking()
        self.toggle_BSOL_tracking()
        self.set_run_table_column_headers_visibility(True)

        self.view.laser_image_button.clicked.connect(self.load_laser_image)

    def set_run_table_column_headers_visibility(self, visible):
        # header_label_list = ["Load", "Run ID", "Plot", "Legend"]
        # self.view.run_parameters_table.setRowCount(len(header_label_list))
        # self.view.run_parameters_table.setHorizontalHeaderLabels(header_label_list)
        self.view.run_parameters_table.horizontalHeader().setVisible(visible)
        self.set_up_step_size_buttons()
        self.threadpool = QThreadPool()
        self.view.total_threads.setMaximum(self.threadpool.maxThreadCount())
        self.threadpool.setMaxThreadCount(self.threadpool.maxThreadCount()/2)
        self.view.total_threads.setValue(self.threadpool.maxThreadCount())
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
        astra_use_wsl = int(os.environ['WSL_ASTRA']) if 'WSL_ASTRA' in os.environ else 1
        self.view.WSL_ASTRA_threads.setValue(astra_use_wsl)
        self.view.total_threads.valueChanged.connect(self.set_total_threads)
        self.view.WSL_ASTRA_threads.valueChanged.connect(self.set_WSL_ASTRA_threads)

    def set_total_threads(self, value):
        self.threadpool.setMaxThreadCount(value)

    def set_WSL_ASTRA_threads(self, value):
        self.model.data.Framework.global_parameters['astra_use_wsl'] = value
        self.model.data.Framework.defineASTRACommand()

    def set_base_directory(self, directory):
        """ Change the base directory the model starts in """
        self.model.set_base_directory(directory)

    def create_datatree_widget(self):
        """ Create the YAML tree widget """
        # self.view.yaml_tree_widget = pg.DataTreeWidget()
        # layout = self.view.run_splitter
        # layout.addWidget(self.view.yaml_tree_widget)
        table = self.view.run_parameters_table
        table.clicked.connect(self.show_yaml_in_datatree)
        table.horizontalHeader().setVisible(True)
        table.setSortingEnabled(True)
        # table.horizontalHeader().setResizeMode(QHeaderView.Stretch)
        table.setShowGrid(True)
        table.setSelectionBehavior(QTableView.SelectRows)
        table.setAlternatingRowColors(True)
        table.setColumnWidth(0,10)
        table.setColumnWidth(2,10)
        table.setColumnWidth(3,10)
        self.tablemodel = run_table.RunModel(data=[],timestamps=[], rpc=self)
        # Doesn't appear
        #proxyModel = QSortFilterProxyModel()
        #proxyModel.setSourceModel(self.tablemodel)
        table.setModel(self.tablemodel)
        table.setSortingEnabled(True)
        table.setItemDelegateForColumn(0, run_table.LoadButtonDelegate(table, self))
        table.setItemDelegateForColumn(2, run_table.PlotCheckboxDelegate(table, self))
        table.setItemDelegateForColumn(3, run_table.PlotColorDelegate(table, self))
        table.setItemDelegateForColumn(4, run_table.DateDelegate(table))

    def show_yaml_in_datatree(self, item):
        """ Update the YAML tree widget based on row and column from the run table """
        row = item.row()
        table = self.view.run_parameters_table
        runno = item.siblingAtColumn(1).data()
        data = self.model.import_yaml(runno)
        guidata = create_yaml_dictionary(self.model.data)
        ddiff = DeepDiff(data, guidata, ignore_order=True, exclude_paths={"root['runs']"})
        table = []
        if 'values_changed' in ddiff:
            for k,v in ddiff['values_changed'].items():
                split = self.table_match.findall(k)
                table.append({'Lattice\t': split[0], 'Element\t': split[1], 'Property\t': split[2], 'Run Value\t': str(v['old_value']), 'Current Value\t': str(v['new_value'])})
        self.view.yaml_tree_widget.setData(table)

    def emit_run_id_clicked_signal(self, row, col):
        """ Emit a signal when a table item is clicked """
        table = self.view.run_parameters_table
        runno = table.item(row, self.run_table_columns['run_id']).text()
        self.run_id_clicked.emit(str(runno))

    def emit_sort_by_timestamp_signal(self, column, order):
        table = self.view.run_parameters_table
        if column == 4:
            table.sortByColumn(column, order)

    def populate_run_parameters_table(self):
        """ Reset the run table with new data """
        timer = QElapsedTimer()
        timer.start()
        table = self.view.run_parameters_table
        model = table.model()
        if model is not None:
            table.setModel(None)
            model.deleteLater()
        dirnames = self.model.get_all_directory_names()
        timestamps = self.model.get_all_run_timestamps()
        self.tablemodel = run_table.RunModel(list(reversed(dirnames)),timestamps, self)
        table.setModel(self.tablemodel)
        table.setColumnWidth(0,12)
        table.setColumnWidth(1,228)
        table.setColumnWidth(2,12)
        table.setColumnWidth(3,12)
        table.setColumnWidth(4,228)

    def refresh_run_parameters_table(self):
        table = self.view.run_parameters_table
        model = table.model()
        model.modelReset.emit()
        model.sort(4,model.currentSortDirection)

    def update_run_parameters_table(self):
        """ Update the run table data and refresh the view """
        table = self.view.run_parameters_table
        model = table.model()
        dirnames = self.model.get_all_directory_names()
        timestamps = self.model.get_all_run_timestamps()
        model.update_data(list(reversed(dirnames)), timestamps)
        model.modelReset.emit()

    def refresh_run_parameters_table(self):
        """ Refresh the run table view """
        table = self.view.run_parameters_table
        model = table.model()
        model.modelReset.emit()

    def delete_run_id(self, run_id):
        """ Delete a run_id """
        self.delete_run_id_signal.emit(run_id)
        self.refresh_run_parameters_table()

    def setrunplotcolor(self, row, color):
        """ Update the run table with the correct plotting color """
        self.update_run_parameters_table()
        table = self.view.run_parameters_table
        run_id = table.model()._data[row]
        self.run_plot_colors[run_id] = color
        self.refresh_run_parameters_table()

    def enable_plot_on_id(self, id):
        """ Enable plotting based on a run_id """
        self.update_run_parameters_table()
        table = self.view.run_parameters_table
        row = table.model()._data.index(id)
        self.emit_plot_signals(row, id, True)
        self.refresh_run_parameters_table()

    def enable_plot_on_row(self, row):
        """ Enable plotting based on a table row number """
        self.update_run_parameters_table()
        table = self.view.run_parameters_table
        item = table.model()._data[row]
        self.emit_plot_signals(row, item, True)
        self.refresh_run_parameters_table()

    def get_id_for_row(self, row):
        """ Find run id for a run table row """
        table = self.view.run_parameters_table
        item = table.model()._data[row]
        return item

    def clear_all_plots(self):
        """ For each row in the run table disable plotting """
        [self.remove_plot_signal.emit(v) for v in self.run_plots]
        self.run_plots = []
        self.run_plot_colors = {}
        self.refresh_run_parameters_table()

    def open_folder_on_server(self, dir):
        remote_dir = self.model.get_absolute_folder_location(dir)
        os.startfile(remote_dir)

    def emit_plot_signals(self, k, v, state):
        """ Enable/disable plotting if a plot checkbox has been clicked """
        if state and not v in self.run_plots:
            self.run_plots.append(v)
            self.add_plot_signal.emit(k,v)
        elif not state and v in self.run_plots:
            self.run_plots.remove(v)
            del self.run_plot_colors[v]
            self.remove_plot_signal.emit(v)
        self.refresh_run_parameters_table()


    def toggle_BSOL_tracking(self):
        """ Connect/Diconnect the BSOL tracking functions """
        widget = self.view.bsol_track_checkBox
        if widget.isChecked():
            self.view.buckingsol_strength.setEnabled(False)
            self.view.sol_strength.valueChanged.connect(self.set_BSOL_tracked_value)
            self.view.sol_strength.valueChanged.emit(self.view.sol_strength.value())
        else:
            self.view.buckingsol_strength.setEnabled(True)
            try:
                self.view.sol_strength.valueChanged.disconnect(self.set_BSOL_tracked_value)
            except:
                pass

    def set_BSOL_tracked_value(self, value):
        """ Update the BSOL value to track the main SOL """
        self.view.buckingsol_strength.setValue(float(-0.9*value))

    def update_macro_particle_combo(self):
        """ Update the macro particle combobox with valid entries """
        combo = self.view.macro_particle
        for i in range(4,7):
            combo.addItem(str(2**(3*i)), i)
        combo.setCurrentIndex(0)

    def split_accessible_name(self, aname):
        """ Split an accessible name based on length """
        if len((aname.split(':'))) == 3:
            dictname, pv, param = map(str, aname.split(':'))
        elif len((aname.split(':'))) == 2:
            param = None
            dictname, pv = map(str, aname.split(':'))
        else:
            print('Problem with name:', aname)
            param = None
            dictname = None
            pv = None
        return dictname, pv, param

    def get_widget_value(self, widget):
        """ Get a widgets value based on widget type """
        widget_type = type(widget)
        if widget_type is QLineEdit:
            try:
                value = float(widget.text())
            except:
                value = str(widget.text())
        elif widget_type is QDoubleSpinBox:
            value = round(float(widget.value()), widget.decimals())
        elif widget_type is QSpinBox:
            value = int(widget.value())
        elif widget_type is QCheckBox:
            value = True if widget.isChecked() else False
        elif widget_type is QComboBox:
            value = widget.itemData(widget.currentIndex())
            if value == '' or value is None:
                value = str(widget.currentText())
            if isinstance(value, QVariant):
                value = value.toString()
            value = str(value)
        elif isinstance(widget, CheckableComboBox):
            value = widget.getCheckedTags()
        elif isinstance(widget, userWidget) or isinstance(widget, timeWidget):
            value = str(widget.value())
        else:
            print('Widget Error! Type = ', type(widget))
            value = None
        return value

    @pyqtSlot()
    def update_value_in_dict(self):
        """ Update the data object when a widget emits an update signal """
        widget = self.sender()
        dictname, pv, param = self.split_accessible_name(widget.accessibleName())
        value = self.get_widget_value(widget)
        if param is None:
            try:
                self.model.data.parameterDict[dictname].update({pv: value})
            except:
                print('Error ', dictname, pv, value)
        else:
            try:
                self.model.data.parameterDict[dictname][pv].update({param: value})
            except:
                print('Error ', dictname, pv, param, value)

    def analyse_children(self, layout):
        """ Connect widgets and force an update based on a layout """
        accessibleNames = {}
        childCount = layout.count()
        for child in range(0,childCount):
            widget = layout.itemAt(child).widget()
            if widget is not None and widget.accessibleName() is not None and not widget.accessibleName() == "":
                accessibleNames[widget.accessibleName()] = widget
            else:
                pass
        for k, v in accessibleNames.items():
            widget = v
            if type(widget) is QLineEdit:
                widget.textChanged.connect(self.update_value_in_dict)
                widget.textChanged.emit(widget.placeholderText())
            elif type(widget) is QDoubleSpinBox or type(widget) is QSpinBox:
                widget.valueChanged.connect(self.update_value_in_dict)
                widget.valueChanged.emit(widget.value())
                self.scannableParameters.append(str(widget.accessibleName()))
            elif type(widget) is QCheckBox:
                value = True if widget.isChecked() else False
                widget.stateChanged.connect(self.update_value_in_dict)
                widget.stateChanged.emit(widget.isChecked())
            elif type(widget) is QComboBox:
                widget.currentIndexChanged.connect(self.update_value_in_dict)
                widget.currentIndexChanged.emit(widget.currentIndex())
            elif isinstance(widget, CheckableComboBox):
                # print('analyse_children: CheckableComboBox! ', widget)
                widget.tagChanged.connect(self.update_value_in_dict)
                widget.tagChanged.emit()
            elif isinstance(widget, userWidget):
                widget.update.connect(self.update_value_in_dict)
                widget.update.emit()
            elif isinstance(widget, timeWidget):
                widget.update.connect(self.update_value_in_dict)
                widget.update.emit()
                self.view.runButton.clicked.connect(widget.update.emit)
            self.accessibleNames[k] = v

    def trigger_children(self, layout):
        """ Force widgets to emit update signals based on a layout """
        accessibleNames = {}
        childCount = layout.count()
        for child in range(0,childCount):
            widget = layout.itemAt(child).widget()
            if widget is not None and widget.accessibleName() is not None and not widget.accessibleName() == "":
                accessibleNames[widget.accessibleName()] = widget
            else:
                pass
        for k, v in accessibleNames.items():
            widget = v
            if type(widget) is QLineEdit:
                widget.textChanged.emit(widget.placeholderText())
            elif type(widget) is QDoubleSpinBox or type(widget) is QSpinBox:
                widget.valueChanged.emit(widget.value())
            elif type(widget) is QCheckBox:
                widget.stateChanged.emit(widget.isChecked())
            elif type(widget) is QComboBox:
                widget.currentIndexChanged.emit(widget.currentIndex())
            elif isinstance(widget, CheckableComboBox):
                # print('analyse_children: CheckableComboBox! ', widget)
                widget.tagChanged.emit()
            elif isinstance(widget, userWidget):
                widget.update.emit()
            elif isinstance(widget, timeWidget):
                widget.update.emit()

    def remove_children(self, layout):
        """ Disconnect and remove widgets based on a layout """
        accessibleNames = {}
        childCount = layout.count()
        for child in range(0,childCount):
            widget = layout.itemAt(child).widget()
            if widget is not None and widget.accessibleName() is not None and not widget.accessibleName() == "":
                accessibleNames[widget.accessibleName()] = widget
            else:
                pass
        for k, v in accessibleNames.items():
            # print('Removing widget ', widget)
            widget = v
            if type(widget) is QLineEdit:
                widget.textChanged.disconnect()
            elif type(widget) is QDoubleSpinBox or type(widget) is QSpinBox:
                widget.valueChanged.disconnect()
            elif type(widget) is QCheckBox:
                widget.stateChanged.disconnect()
            elif type(widget) is QComboBox:
                widget.currentIndexChanged.disconnect()
            elif isinstance(widget, CheckableComboBox):
                widget.tagChanged.disconnect()
            elif isinstance(widget, userWidget):
                widget.update.disconnect()
            elif isinstance(widget, timeWidget):
                widget.update.disconnect()
            widget.deleteLater()
            if k in self.accessibleNames:
                del self.accessibleNames[k]

    def initialize_run_parameter_data(self):
        """ Initialise the data object based on available widgets """
        self.scannableParameters = []
        for layout in self.formLayoutList:
            self.analyse_children(layout)

    def get_scannable_parameters_dict(self):
        """ Create a list of available scanning parameters """
        scannableParameterDict = collections.OrderedDict()
        unscannableParameters = ['macro_particle', 'injector_space_charge',
                                 'rest_of_line_space_charge', 'end_of_line']
        for key in self.scannableParameters:
            if key not in unscannableParameters:
                if ':' in key:
                    scannableParameterDict[' - '.join(list(key.split(':')))] = key
        return scannableParameterDict

    def populate_scan_combo_box(self, id=1):
        """ Update the list of available scanning parameters for a new scan tab """
        scanParameterComboBox = self.view.scan_tabWidget.tabs[id]
        scanParameterComboBox.addItems(self.model.data.scannableParametersDict)
        self.model.data.initialise_scan(id)
        self.analyse_children(self.view.scan_tabWidget.tabs[id].layout)

    def remove_scan_dict(self, layout):
        """ Delete a scan entry in the data object """
        self.remove_children(layout)
        self.model.data.scanDict = self.model.data.parameterDict['scan'] = collections.OrderedDict()
        for k,v in self.view.scan_tabWidget.tabs.items():
            self.model.data.initialise_scan(k)
            self.trigger_children(v.layout)

    def update_widget_from_dict(self, aname):
        """ Update a widgets value from the data object """
        widget = self.get_object_by_accessible_name(aname)
        dictname, pv, param = self.split_accessible_name(aname)
        if param is None:
            value = self.model.data.parameterDict[dictname][pv]
        else:
            value = self.model.data.parameterDict[dictname][pv][param]
        self.update_widgets_with_values(aname, value)

    def get_object_by_accessible_name(self, aname):
        """ Find a widget based on it's accessible name """
        if aname in self.accessibleNames:
            return self.accessibleNames[aname]
        else:
            return None

    def update_widgets_with_values(self, aname, value):
        """ Update a widgets value based on it's accessible name """
        if isinstance(value, (dict)):
            for k,v in value.items():
                self.update_widgets_with_values(aname.replace('Dict','')+':'+str(k),v)
        else:
            widget = self.get_object_by_accessible_name(aname)
            if widget is not None:
                if type(widget) is QLineEdit:
                    widget.setText(str(value))
                elif type(widget) is QDoubleSpinBox:
                    widget.setValue(float(value))
                elif type(widget) is QSpinBox:
                    widget.setValue(int(value))
                elif type(widget) is QCheckBox:
                    if value is True:
                        widget.setChecked(True)
                    else:
                        widget.setChecked(False)
                elif type(widget) is QComboBox:
                    index = widget.findText(str(value))
                    # print('combo:',widget.objectName(),'value = ', value, 'index = ', index)
                    if index == -1:
                        index = widget.findData(value)
                        # print('  data index = ', index)
                    widget.setCurrentIndex(index)
                elif isinstance(widget, CheckableComboBox):
                    widget.setTagStates(value)
            # else:
            #     print(aname, widget)

    ## Need to port this to the unified controller
    @pyqtSlot()
    def import_parameter_values_from_yaml_file(self, filename=None, directory=None):
        """ Import a YAML file and update widgets """
        if filename is None:
            dialog = QFileDialog()
            filename = QFileDialog.getOpenFileName(dialog, caption='Open file',
                                                         directory=self.model.data.parameterDict['runs']['directory'],
                                                         filter="YAML files (*.YAML *.YML *.yaml *.yml)")
        filename = filename[0] if isinstance(filename,tuple) else filename
        filename = str(filename)
        if directory is not None and filename is not None:
            filename = os.path.join(directory, filename)
        if not filename == '' and not filename is None and (filename[-4:].lower() == '.yml' or filename[-5:].lower() == '.yaml'):
            loaded_parameter_dict = yaml_parser.parse_parameter_input_file(filename)
            self.load_scans_from_dict(loaded_parameter_dict)
            self.update_widgets_from_yaml_dict(loaded_parameter_dict)
        else:
            print('Failed to import, please provide a filename')

    def load_yaml_from_db(self, run_id):
        """ Import a YAML based on run_id """
        loaded_parameter_dict = self.model.import_yaml(run_id)
        self.load_scans_from_dict(loaded_parameter_dict)
        self.update_widgets_from_yaml_dict(loaded_parameter_dict)

    def load_scans_from_dict(self, loaded_parameter_dict):
        """ Initialise the scanning tabs from a YAML dictionary """
        if 'scan' in loaded_parameter_dict:
            ntabs = len(loaded_parameter_dict['scan'].keys())
            self.view.scan_tabWidget.clear()
            self.model.data.scanDict = self.model.data.parameterDict['scan'] = collections.OrderedDict()
            self.view.scan_tabWidget.addScanTab()
            while self.view.scan_tabWidget.tab.count() < ntabs:
                self.view.scan_tabWidget.addScanTab()

    def update_widgets_from_yaml_dict(self, loaded_parameter_dict):
        """ Update widgets from a YAML dictionary """
        for (parameter, value) in loaded_parameter_dict.items():
                self.update_widgets_with_values(parameter, value)

    def export_parameter_values_to_yaml_file(self, auto=False, filename=None, directory=None):
        """ Export the current GUI values to a YAML file """
        if auto is True:
            self.model.export_parameter_values_to_yaml_file(auto=True)
            return
        elif filename is None and directory is None:
            dialog = QFileDialog()
            filename, _filter = QFileDialog.getSaveFileName(dialog, caption='Save File', directory='.',
                                                                 filter="YAML Files (*.YAML *.YML *.yaml *.yml")
            filename = filename[0] if isinstance(filename,tuple) else filename
            directory, filename = os.path.split(filename)
        if directory is None:
            directory = '.'
        self.model.export_parameter_values_to_yaml_file(auto=False, filename=filename, directory=directory)

    def disable_run_button(self, scan=False):
        """ Disable the run button, disconnect it and disable all widgets """
        for k, v in self.accessibleNames.items():
            v.setEnabled(False)
        if scan:
            self.view.runButton.setEnabled(True)
            self.view.runButton.clicked.disconnect(self.app_sequence)
            self.view.runButton.setText('Abort')
            self.view.runButton.clicked.connect(self.abort_ongoing_scan)

    def read_from_epics(self, time_from=None, time_to=None):
        """ Read values from EPICS and update widgets """
        for l in self.model.data.lattices:
            self.model.data.read_values_from_epics(self.model.data.parameterDict[l])
            for key, value in self.model.data.parameterDict[l].items():
                if value['type'] == "quadrupole":
                    self.update_widgets_with_values(l + ':' + key + ':k1l', value['k1l'])
                if value['type'] == "solenoid":
                    self.update_widgets_with_values(l + ':' + key + ':field_amplitude', value['field_amplitude'])
                if value['type'] == "cavity":
                    self.update_widgets_with_values(l + ':' + key + ':phase', value['phase'])
                    self.update_widgets_with_values(l + ':' + key + ':field_amplitude', value['field_amplitude'])
        self.model.data.read_values_from_epics(self.model.data.parameterDict['generator'])
        for key, value in self.model.data.parameterDict['generator'].items():
            if key == "charge":
                self.update_widgets_with_values('generator:' + key + ':value', value['value'])
        return

    def read_from_DBURT(self, DBURT=None):
        """ Read a DBURT and update widgets """
        if DBURT is None or DBURT is False:
            DBURT = "//fed.cclrc.ac.uk/Org/NLab/ASTeC/Projects/VELA/Snapshots/DBURT/CLARA_2_BA1_BA2_2020-03-09-1602_5.5MeV Beam Transport.dburt"
        print('reading DBURT ', DBURT)
        data = self.model.data.read_values_from_DBURT(DBURT)
        for key, magnet in data.items():
            value = magnet['value']
            if value['type'] == "quadrupole":
                print(magnet['lattice'] + ':' + magnet['fullname'] + ':k1l', value['k1l'])
                self.update_widgets_with_values(magnet['lattice'] + ':' + magnet['fullname'] + ':k1l', value['k1l'])
            if value['type'] == "solenoid":
                print(magnet['lattice'] + ':' + magnet['fullname'] + ':field_amplitude', value['field_amplitude'])
                self.update_widgets_with_values(magnet['lattice'] + ':' + magnet['fullname'] + ':field_amplitude', value['field_amplitude'])
            if value['type'] == "cavity":
                self.update_widgets_with_values(magnet['fullname'] + ':phase', value['phase'])
                self.update_widgets_with_values(magnet['fullname'] + ':field_amplitude', value['field_amplitude'])
        return

    def abort_ongoing_scan(self):
        self.abort_scan = True

    def enable_run_button(self):
        """ Enable the run button, re-connect it and re-enable all widgets """
        self.view.runButton.setText('Track')
        try:
            self.view.runButton.clicked.disconnect(self.app_sequence)
        except:
            try:
                self.view.runButton.clicked.disconnect(self.abort_ongoing_scan)
            except:
                pass
        for k, v in self.accessibleNames.items():
            v.setEnabled(True)
        self.view.runButton.clicked.connect(self.app_sequence)
        return

    def generate_scan_range(self, dimension=1):
        """ Retrieve scanning tab parameters """
        dimension = str(dimension)
        do_scan = self.model.data.scanDict[dimension]['scan']
        if do_scan:
            scan_start = float(self.model.data.scanDict[dimension]['scan_from_value'])
            scan_end = float(self.model.data.scanDict[dimension]['scan_to_value'])
            scan_step_size = float(self.model.data.scanDict[dimension]['scan_step_size'])
            parameter = self.model.data.scanDict[dimension]['parameter']
            return do_scan, scan_start, scan_end, scan_step_size, parameter, self.model.data.lattices.index(self.split_accessible_name(parameter)[0])
        else:
            return None

    def generate_scan_dictionary(self):
        """ Generate a multi-dimensional list of scanning parameters and their values """
        # Generate all scanning data
        # Find Tab id's
        tab_ids = [tab.id for tab in self.view.scan_tabWidget.tabs.values()]
        # Generate the relvant scan data for each scanning tab - if scan is not on, returns None - ignore these ones
        prescancombineddata = [self.generate_scan_range(i) for i in tab_ids if self.generate_scan_range(i) is not None]
        # We need to sort the tabs into lattice order (makes it faster later!)
        scancombineddata = sorted(prescancombineddata, key=lambda pscd: pscd[5])
        # Count Trues to find number of dimensions (in theory they should all be True...)
        ndims = np.sum([s[0] for s in scancombineddata])
        # Select data where do_scan is True (should be all of them, but...)
        scan_data = [s for s in scancombineddata if s[0] is True]
        # Generate slice indexes based on selected data
        # s[1] = start, s[2] = end, s[3] = step
        # Add 1e-15 to end point as mgrid is not inclusive...
        idx = tuple(slice(s[1], s[2] + 1e-15, s[3]) for s in scan_data)
        # Generate values for each dimension
        grid = np.mgrid[idx].reshape(ndims,-1).T
        # get list of params
        params = [scan[4] for scan in scan_data]
        # for each param generate correct length of list, then transpose them a
        # few times to get in [[param1, value1], [param2, value2]...] blocks for each step of the scan
        return [list(zip(*a)) for a in zip(*[[params for i in range(len(grid))], grid])]

    def setup_scan(self):
        """ Initialise the scanning lists """
        # Generate list of scanning lists to scan over
        self.scanning_grid = self.generate_scan_dictionary()
        # Save the original values, so we can reset them later
        self.scan_basevalues = [[aname, self.get_widget_value(self.get_object_by_accessible_name(aname))] for aname, value in self.scanning_grid[0]]
        # Reset the progressbar
        self.scan_no = 0
        self.view.progressBar.setMinimum(0)
        self.view.progressBar.setMaximum(int(len(self.scanning_grid)))
        self.view.progressBar.setValue(0)
        # Start the scanning loop
        self.continue_scan()

    def do_scan(self, data, doPlot, nthreads=0):
        """ Perform a scan step in a thread """
        # Instantiate a new Model, setting the data to a copy of the Data class
        localmodel = Model(dataClass=data)
        # Use the same dbcontroller - NOTE: cannot write to DB in thread! Reading from DB only.
        localmodel.dbcontroller = self.model.dbcontroller
        # Ensure model directory location is consistent
        localmodel.basedirectoryname = self.model.basedirectoryname
        # Run the model script
        try:
            tracking_success = localmodel.run_script()
        except:
            tracking_success = False
        # Emit signal that the script has finished. This will be connected in the MAIN thread!
        self.run_finished_signal.emit(tracking_success, doPlot, localmodel.directoryname, localmodel.yaml, nthreads)
        if tracking_success:
            # If run was successful save the YAML in the thread's model directory
            localmodel.export_parameter_values_to_yaml_file(auto=True)

    def check_lattices_to_be_scanned(self, current_scan):
        """ Check if a scan requires an initialisation step or not """
        # Find out which lattice the scan is taking place in
        # List all lattices that will be changed (using the accessible name of the variable)
        scan_variable_lattices = [self.split_accessible_name(cs[0])[0] for cs in current_scan]
        # Find the last lattice index in the beamline
        scan_variable_index = max([self.model.data.lattices.index(svl) for svl in scan_variable_lattices])
        # Find the lattice name equivalent
        scan_variable_lattice = self.model.data.lattices[scan_variable_index]
        # Create a YAML dictionary to do the compare against
        yaml = create_yaml_dictionary(self.model.data)
        # Now we check which lattice's need to be re-run - if it's not the same as (or greater than!) the scan_variable_lattice then we need to do a run NOT in parallel
        closest_match, lattices_to_be_saved = self.model.dbcontroller.reader.find_lattices_that_dont_exist(yaml)
        # We might not need to re-run at all!
        if lattices_to_be_saved is not None and len(lattices_to_be_saved) > 0:
            # If we can't find the lattice then we just assume "run everything!"
            if lattices_to_be_saved[0] in self.model.data.lattices:
                return self.model.data.lattices.index(lattices_to_be_saved[0]) >= self.model.data.lattices.index(scan_variable_lattice)
            else:
                return False
        return None

    def continue_scan(self):
        """ Iterate the scan """
        # Check we haven't finished the scanning, or it hasn't been aborted
        if not self.abort_scan and self.scan_no < len(self.scanning_grid):
            # This is the scan we are doing
            current_scan = self.scanning_grid[self.scan_no]
            # Update the widgets with their new values
            for aname, value in current_scan:
                self.update_widgets_with_values(aname, value)
                value = self.get_widget_value(self.get_object_by_accessible_name(aname))
                print('Scanning['+str(self.scan_no)+']: Setting ', aname, ' to ', value, ' - ACTUAL Value = ', self.get_widget_value(self.get_object_by_accessible_name(aname)))
            # Check to see if we need to pre-run some sections of the lattice
            lattice_is_initial = self.check_lattices_to_be_scanned(current_scan)
            # Make a copy of the data object to pass through to the worker thread (we make a copy so we don't change it when in parallel)
            data = deepcopy(self.model.data)
            # We need to confirm if we will be running ASTRA using WSL (which may use more threads)
            nthreads = self.model.are_we_using_WSL_ASTRA() - 1
            for i in range(nthreads):
                self.threadpool.reserveThread()
            # Create the worker thread
            worker = GenericWorker(self.do_scan, data, self.view.autoPlotCheckbox.isChecked(), nthreads)
            # If we have to run an initial run to set-up the database do it here - we don't continue until the "finished" signal is sent
            if lattice_is_initial is False:
                print('Running initial setup!')
                worker.signals.finished.connect(self.continue_scan)
            # Start the worker thread using the threadpool
            self.threadpool.start(worker)
            # iterate the scan number
            self.scan_no += 1
            # If this is a normal run (not an initialisation run) we can go onto the next scan step
            if lattice_is_initial is None or lattice_is_initial is True:
                self.continue_scan()
        else:
            # We have finished or aborted
            if self.abort_scan:
                # Reset everything
                self.enable_run_button()
                self.reset_progress_bar_timer()
            for aname, value in self.scan_basevalues:
                # Restore original widget values in the GUI
                self.update_widgets_with_values(aname, value)
            # reset the Abort variable
            self.abort_scan = False

    def check_scan_parameters(self):
        """ Check all of the scanning parameters are valid """
        # We only return True if we don't return False in the meantime
        for tab in self.view.scan_tabWidget.tabs.values():
            if tab.scanCheckbox.isChecked(): # Only check the scan tabs that are being used
                try:
                    scan_start = float(self.model.data.scanDict[str(tab.id)]['scan_from_value'])
                    scan_end = float(self.model.data.scanDict[str(tab.id)]['scan_to_value'])
                    scan_step_size = float(self.model.data.scanDict[str(tab.id)]['scan_step_size'])
                    # Create the scan range using arange
                    scan_range = np.arange(scan_start, scan_end + scan_step_size, scan_step_size)
                    # If the scan_range is not valid it will be zero length
                    if not len(scan_range) > 0:
                        return False
                except ValueError:
                    return False
        return True

    def check_if_scanning(self):
        """ Check if we need to do a scan """
        # Get the scanCheckBox states
        scanning = [tab.scanCheckbox.isChecked() for tab in self.view.scan_tabWidget.tabs.values()]
        # If any scanCheckBoxes are True, we are scanning
        return any(scanning)

    def app_sequence(self):
        """ Main tracking sequence """
        self.progress = 0
        if self.check_if_scanning(): # Are we scanning?
            if self.check_scan_parameters(): # Are the scanning parameters valid
                self.disable_run_button(scan=True)
                self.setup_scan()
            else:
                print('Error in scan parameters - aborting!')
                return
        else:
            self.disable_run_button(scan=False)
            # Reset progressbar
            self.view.progressBar.setMinimum(0)
            self.view.progressBar.setMaximum(1)
            self.view.progressBar.setValue(0)
            nthreads = self.model.are_we_using_WSL_ASTRA() - 1
            for i in range(nthreads):
                self.threadpool.reserveThread()
        # Make a copy of the data object
            data = deepcopy(self.model.data)
            # Create a single worker
            worker = GenericWorker(self.do_scan, data, self.view.autoPlotCheckbox.isChecked(), nthreads)
            # Start the worker
            self.threadpool.start(worker)
        return

    def run_finished(self, success, doPlot, directoryname, yaml, nthreads=0):
        """ Check outcome of a worker-thread """
        # Release any extra threads
        for i in range(nthreads):
            self.threadpool.releaseThread()
        # Increment the progress so far
        self.progress += 1
        # Update the progressbar
        self.view.progressBar.setValue(self.progress)
        if self.progress >= self.view.progressBar.maximum(): # We have finished all runs
            self.enable_run_button()
            self.reset_progress_bar_timer()
        # print('run_finished!', directoryname)
        if success: # The worker thread finished successfully, so save it
            self.model.save_settings_to_database(yaml, directoryname)
            self.update_runs_widget(plot=doPlot, id=directoryname)
            self.update_directory_widget(dirname=directoryname)

    def update_directory_widget(self, dirname=None):
        """ Update the directory widget with a new value """
        if dirname is None:
            dirname = self.model.get_directory_name()
        self.update_widgets_with_values('runs:directory', dirname)

    def update_runs_widget(self, plot=False, id=None):
        """ Add run to run table, and plot if selected """
        self.update_run_parameters_table()
        if plot and id is not None:
            self.enable_plot_on_id(id)

    def reset_progress_bar_timer(self):
        """ After 1s set the progressbar back to zero """
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.view.progressBar.reset)
        self.timer.start()

    ##### User tags

    def create_user_tag_combo_box(self):
        self.tagWidgets = {}
        self.view.userTagComboBox = CheckableComboBox()
        self.view.userTagComboBox.setAccessibleName('runs:tags')
        self.view.userTagComboBox.addItem('User Tags')
        for t in self.tags:
            self.view.userTagComboBox.addCheckableItem(t)
        self.view.username = userWidget()
        self.view.username.setAccessibleName('runs:username')
        self.view.username.hide()
        self.view.time = timeWidget()
        self.view.time.setAccessibleName('runs:timestamp')
        self.view.time.hide()

        self.view.tags_Layout.addWidget(self.view.userTagComboBox,0,0,1,2)
        self.view.tags_Layout.addWidget(self.view.username,1,0,1,1)
        self.view.tags_Layout.addWidget(self.view.time,1,1,1,1)

    def change_database(self, database=False):
        if database is False:
            dialog = QFileDialog()
            database, _filter = QFileDialog.getSaveFileName(dialog, caption='Database File', directory='.',
                                                                 filter="SQLite Files (*.db)", options=QFileDialog.DontConfirmOverwrite	)
        if database is not False and database is not None and isinstance(database, str):
            self.change_database_signal.emit(database)

    def database_changed(self):
        self.update_run_parameters_table()

    ##### User tags

    def set_up_step_size_buttons(self):
        buttongroups = {'CLA_S02_stepsize': 'CLA-S02', 'CLA_C2V_stepsize': 'CLA-C2V', 'EBT_INJ_stepsize': 'EBT-INJ', 'EBT_BA1_stepsize': 'EBT-BA1'}
        for bgname, lattice in buttongroups.items():
            bg = getattr(self.view, bgname)
            bg.setProperty('lattice', lattice)
            bg.buttonClicked.connect(self.stepButtonClicked)
        for bgname, latt in buttongroups.items():
            button = getattr(self.view, 'stepsize_0001_'+latt.replace('-','_'))
            button.click()

    def stepButtonClicked(self, button):
        # lattice = '-'.join(button.objectName().split('_')[2:])
        lattice = self.sender().property('lattice')
        step = float(button.text())
        """ Change the step size of the magnet widgets (only those with k1l parameters) """
        accessibleNames = {}
        for layout in self.formLayoutList:
            childCount = layout.count()
            for child in range(0,childCount):
                widget = layout.itemAt(child).widget()
                if widget is not None and 'k1l' in widget.accessibleName() and lattice in widget.accessibleName() and isinstance(widget, QDoubleSpinBox):
                    accessibleNames[widget.accessibleName()] = widget
                else:
                    pass
        for k, widget in accessibleNames.items():
            widget.setSingleStep(step)

#####  Laser button widget

    def load_laser_image(self, button):
        dialog = QFileDialog()
        filename = QFileDialog.getOpenFileName(dialog, caption='Open file',
                                                     directory='.',
                                                     filter="BMP files (*.bmp)")
        filename = os.path.relpath(filename[0]) if isinstance(filename,tuple) else filename
        self.view.laser_image_lineedit.setText(filename)
