try:
    from PyQt4.QtCore import *
    from PyQt4.QtGui import *
except:
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *
import database.run_parameters_parser as yaml_parser
from model.local_model import create_yaml_dictionary
import sys, os
import time
import collections
import numpy as np
import pyqtgraph as pg
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
    run_id_clicked = pyqtSignal(str)

    tags = ['BA1', 'User Experiment', 'Front End', 'Emittance', 'Energy Spread', 'Commissioning']

    run_table_columns = {'run_id': 1, 'load_run_button': 0, 'plot_checkbox': 2, 'plot_color': 3}

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
                               self.view.tags_groupBox,
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
        self.populate_scan_combo_box()
        self.view.parameter_scan.stateChanged.connect(lambda: self.toggle_scan_parameters_state(self.view.parameter_scan))
        self.view.bsol_track_checkBox.stateChanged.connect(self.toggle_BSOL_tracking)
        self.view.runButton.clicked.connect(self.run_astra)
        self.view.directory.textChanged[str].emit(self.view.directory.text())
        self.view.clearPlotsButton.clicked.connect(self.clear_all_plots)
        self.abort_scan = False
        self.run_plots = []
        self.run_plot_colors = {}
        self.tracking_success = False
        self.create_datatree_widget()
        self.populate_run_parameters_table()
        self.toggle_BSOL_tracking()
        self.toggle_BSOL_tracking()

    def create_datatree_widget(self):
        # self.view.yaml_tree_widget = pg.DataTreeWidget()
        # layout = self.view.run_splitter
        # layout.addWidget(self.view.yaml_tree_widget)
        table = self.view.run_parameters_table
        table.cellClicked.connect(self.show_yaml_in_datatree)
        table.cellDoubleClicked.connect(self.emit_run_id_clicked_signal)
        table.resizeColumnsToContents()

    def show_yaml_in_datatree(self, row, col):
        table = self.view.run_parameters_table
        runno = table.item(row, self.run_table_columns['run_id']).text()
        data = self.model.import_yaml(runno)
        guidata = create_yaml_dictionary(self.model.data)
        ddiff = DeepDiff(data, guidata, ignore_order=True, exclude_paths={"root['runs']"})
        # print(ddiff)
        self.view.yaml_tree_widget.setData(ddiff)
        # self.run_id_clicked.emit(runno)

    def emit_run_id_clicked_signal(self, row, col):
        table = self.view.run_parameters_table
        runno = table.item(row, self.run_table_columns['run_id']).text()
        # print('clicked run_id = ', runno)
        self.run_id_clicked.emit(str(runno))

    def populate_run_parameters_table(self):
        table = self.view.run_parameters_table
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.clearContents()
        table.setRowCount(0)
        dirnames = self.model.get_all_directory_names()
        for k,v in enumerate(reversed(dirnames)):
            self.add_run_table_row(k, v)

    def add_run_table_row(self, k, v, row=None):
        table = self.view.run_parameters_table
        rowPosition = table.rowCount() if row is None else row
        table.insertRow(rowPosition)
        # table.setItem(rowPosition, 0, QTableWidgetItem(str(int(k))))
        dir = os.path.basename(v)
        table.setItem(rowPosition, self.run_table_columns['run_id'], QTableWidgetItem(str(dir)))
        open_folder_button = QPushButton('Open')
        open_folder_button.setEnabled(False)
        open_folder_button.clicked.connect(lambda : self.open_folder_on_server(dir))
        load_run_button = QPushButton('Load')
        load_run_button.setEnabled(True)
        load_run_button.setMaximumSize(50,50)
        load_run_button.clicked.connect(lambda : self.load_yaml_from_db(dir))
        table.setCellWidget(rowPosition, self.run_table_columns['load_run_button'], load_run_button)
        add_plot_button = QCheckBox('Plot')
        if dir in self.run_plots:
            add_plot_button.setChecked(True)
            self.setrunplotcolor(rowPosition, self.run_plot_colors[dir])
        add_plot_button.stateChanged.connect(lambda x: self.emit_plot_signals(k, v, x))
        table.setCellWidget(rowPosition, self.run_table_columns['plot_checkbox'], add_plot_button)
        table.resizeColumnsToContents()

    def delete_run_id(self, run_id):
        self.delete_run_id_signal.emit(run_id)
        self.populate_run_parameters_table()

    def setrunplotcolor(self, row, color):
        table = self.view.run_parameters_table
        colorWidget = pg.ColorButton()
        colorWidget.setEnabled(False)
        colorWidget.setColor(color)
        table.setCellWidget(row, self.run_table_columns['plot_color'], colorWidget)
        run_id = table.item(row, self.run_table_columns['run_id']).text()
        self.run_plot_colors[run_id] = color

    def enable_plot_on_id(self, id):
        table = self.view.run_parameters_table
        items = table.findItems(id, Qt.MatchExactly)
        for item in items:
            row = item.row()
            checkbox = table.cellWidget(row, self.run_table_columns['plot_checkbox'])
            checkbox.setCheckState(Qt.Checked)
        # self.run_plot_colors[run_id] = color

    def clear_all_plots(self):
        table = self.view.run_parameters_table
        for row in range(0,table.rowCount()):
            checkbox = table.cellWidget(row, self.run_table_columns['plot_checkbox'])
            checkbox.setCheckState(Qt.Unchecked)
        # self.run_plot_colors[run_id] = color

    def open_folder_on_server(self, dir):
        remote_dir = self.model.get_absolute_folder_location(dir)
        os.startfile(remote_dir)

    def emit_plot_signals(self, k, v, state):
        if state == Qt.Checked:
            self.add_plot_signal.emit(k,v)
            self.run_plots.append(v)
        elif state == Qt.Unchecked:
            self.remove_plot_signal.emit(v)
            self.run_plots.remove(v)
            table = self.view.run_parameters_table
            table.removeCellWidget(k, self.run_table_columns['plot_color'])

    def toggle_BSOL_tracking(self):
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
        self.view.buckingsol_strength.setValue(float(-0.9*value))

    def update_macro_particle_combo(self):
        combo = self.view.macro_particle
        for i in range(4,7):
            combo.addItem(str(2**(3*i)), i)
        combo.setCurrentIndex(0)

    def split_accessible_name(self, aname):
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
        if type(widget) is QLineEdit:
            try:
                value = float(widget.text())
            except:
                value = str(widget.text())
        elif type(widget) is QDoubleSpinBox:
            value = round(float(widget.value()), widget.decimals())
        elif type(widget) is QSpinBox:
            value = int(widget.value())
        elif type(widget) is QCheckBox:
            value = True if widget.isChecked() else False
        elif type(widget) is QComboBox:
            value = widget.itemData(widget.currentIndex())
            if value == '' or value is None:
                value = str(widget.currentText())
            if isinstance(value, QVariant):
                value = value.toString()
            value = str(value)
        elif isinstance(widget, CheckableComboBox):
            value = widget.getCheckedTags()
        elif isinstance(widget, userWidget) or isinstance(widget, timeWidget):
            # print('time or user widget = ', widget)
            value = str(widget.value())
        else:
            print('Widget Error! Type = ', type(widget))
            value = None
        return value

    @pyqtSlot()
    def update_value_in_dict(self):
        widget = self.sender()
        dictname, pv, param = self.split_accessible_name(widget.accessibleName())
        value = self.get_widget_value(widget)
        if param is None:
            try:
                self.model.data.parameterDict[dictname].update({pv: value})
            except:
                print('Error ', dictname, pv, value)
                exit()
        else:
            try:
                self.model.data.parameterDict[dictname][pv].update({param: value})
            except:
                print('Error ', dictname, pv, param, value)
                exit()

    def analyse_children(self, layout):
        for k, v in self.accessibleNames.items():
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

    def initialize_run_parameter_data(self):
        self.scannableParameters = []
        for layout in self.formLayoutList:
            self.analyse_children(layout)
        # return self.model.data.latticeDict

    def get_scannable_parameters_dict(self):
        scannableParameterDict = collections.OrderedDict()
        unscannableParameters = ['macro_particle', 'injector_space_charge',
                                 'rest_of_line_space_charge', 'end_of_line']
        for key in self.scannableParameters:
            if key not in unscannableParameters:
                if ':' in key:
                    scannableParameterDict[' - '.join(list(key.split(':')))] = key
        return scannableParameterDict

    def populate_scan_combo_box(self):
        scanParameterComboBox = self.view.parameter
        for (parameterDisplayStr, parameter) in self.model.data.scannableParametersDict.items():
            scanParameterComboBox.addItem(parameterDisplayStr, parameter)

    def update_widget_from_dict(self, aname):
        widget = self.get_object_by_accessible_name(aname)
        dictname, pv, param = self.split_accessible_name(aname)
        if param is None:
            value = self.model.data.parameterDict[dictname][pv]
        else:
            value = self.model.data.parameterDict[dictname][pv][param]
        self.update_widgets_with_values(aname, value)

    def get_object_by_accessible_name(self, aname):
        if aname in self.accessibleNames:
            return self.accessibleNames[aname]
        else:
            return None

    def update_widgets_with_values(self, aname, value):
        if isinstance(value, (dict)):
            for k,v in value.items():
                self.update_widgets_with_values(aname.replace('Dict','')+':'+k,v)
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
                    index = widget.findText(value)
                    # print('combo:',widget.objectName(),'value = ', value, 'index = ', index)
                    if index == -1:
                        index = widget.findData(value)
                        # print('  data index = ', index)
                    widget.setCurrentIndex(index)
                elif isinstance(widget, CheckableComboBox):
                    widget.setTagStates(value)

    ## Need to port this to the unified controller
    @pyqtSlot()
    def import_parameter_values_from_yaml_file(self, filename=None):
        if filename is None:
            dialog = QFileDialog()
            filename = QFileDialog.getOpenFileName(dialog, caption='Open file',
                                                         directory=self.model.data.parameterDict['runs']['directory'],
                                                         filter="YAML files (*.YAML *.YML *.yaml *.yml)")
        filename = filename[0] if isinstance(filename,tuple) else filename
        filename = str(filename)
        if not filename == '' and not filename is None and (filename[-4:].lower() == '.yml' or filename[-5:].lower() == '.yaml'):
            loaded_parameter_dict = yaml_parser.parse_parameter_input_file(filename)
            self.update_widgets_from_yaml_dict(loaded_parameter_dict)
        else:
            print('Failed to import, please provide a filename')

    def load_yaml_from_db(self, run_id):
        loaded_parameter_dict = self.model.import_yaml(run_id)
        self.update_widgets_from_yaml_dict(loaded_parameter_dict)

    def update_widgets_from_yaml_dict(self, loaded_parameter_dict):
        for (parameter, value) in loaded_parameter_dict.items():
                self.update_widgets_with_values(parameter, value)

    def export_parameter_values_to_yaml_file(self, auto=False):
        self.model.export_parameter_values_to_yaml_file(auto=auto)

    def toggle_scan_parameters_state(self, object):
        performScanCheckbox = object
        if performScanCheckbox.isChecked():
            self.view.parameter.setEnabled(True)
            self.view.parameter_scan_from_value.setEnabled(True)
            self.view.parameter_scan_to_value.setEnabled(True)
            self.view.parameter_scan_step_size.setEnabled(True)
            self.update_widget_from_dict('scan:parameter')
            self.update_widget_from_dict('scan:parameter_scan_from_value')
            self.update_widget_from_dict('scan:parameter_scan_to_value')
            self.update_widget_from_dict('scan:parameter_scan_step_size')
        else:
            self.view.parameter.setEnabled(False)
            self.view.parameter_scan_from_value.setEnabled(False)
            self.view.parameter_scan_to_value.setEnabled(False)
            self.view.parameter_scan_step_size.setEnabled(False)

    def disable_run_button(self, scan=False):
        for k, v in self.accessibleNames.items():
            v.setEnabled(False)
        if scan:
            self.view.runButton.setEnabled(True)
            self.view.runButton.clicked.disconnect(self.run_astra)
            self.view.runButton.setText('Abort')
            self.view.runButton.clicked.connect(self.abort_ongoing_scan)


    def read_from_epics(self, time_from=None, time_to=None):
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

    def enable_run_button(self, scan=False):
        self.view.runButton.setText('Track')
        try:
            self.view.runButton.clicked.disconnect(self.run_astra)
        except:
            try:
                self.view.runButton.clicked.disconnect(self.abort_ongoing_scan)
            except:
                pass
        for k, v in self.accessibleNames.items():
            v.setEnabled(True)
        self.view.runButton.clicked.connect(self.run_astra)
        return

    def toggle_finished_tracking(self):
        if self.finished_tracking:
            self.finished_tracking = False
        else:
            self.finished_tracking = True

    def setup_scan(self):
        try:
            scan_start = float(self.model.data.scanDict['parameter_scan_from_value'])
            scan_end = float(self.model.data.scanDict['parameter_scan_to_value'])
            scan_step_size = float(self.model.data.scanDict['parameter_scan_step_size'])
            scan_range = np.arange(scan_start, scan_end + scan_step_size, scan_step_size)
            self.view.progressBar.setRange(0,len(scan_range+1))
        except ValueError:
            print("Enter a numerical value to conduct a scan")
        self.scan_parameter = self.model.data.scanDict['parameter']
        self.scan_basedir = str(self.model.data.parameterDict['runs']['directory'])
        self.scan_basevalue = self.get_widget_value(self.get_object_by_accessible_name(self.scan_parameter))
        dictname, pv, param = self.split_accessible_name(self.scan_parameter)
        self.scan_range = np.arange(scan_start, scan_end + scan_step_size, scan_step_size)
        self.scan_no = 0
        self.continue_scan()

    def do_scan(self):
        self.tracking_success = False
        self.tracking_success = self.model.run_script()
        if self.tracking_success:
            self.export_parameter_values_to_yaml_file(auto=True)

    def continue_scan(self):
        if not self.abort_scan and self.scan_no < len(self.scan_range):
            self.view.progressBar.setValue(self.scan_no+1)
            self.scan_progress = self.scan_no+1
            current_scan_value = round(self.scan_range[self.scan_no], 5)
            self.update_widgets_with_values(self.scan_parameter, current_scan_value)
            self.model.data.scanDict['value'] = self.get_widget_value(self.get_object_by_accessible_name(self.scan_parameter))
            print('Scanning['+str(self.scan_no)+']: Setting ', self.scan_parameter, ' to ', current_scan_value, ' - ACTUAL Value = ', self.get_widget_value(self.get_object_by_accessible_name(self.scan_parameter)))
            dictname, pv, param = self.split_accessible_name(self.scan_parameter)
            # subdir = (self.scan_basedir + '/' + pv + '_' + str(current_scan_value)).replace('//','/')
            self.update_widgets_with_values('runs:directory', self.scan_basedir)
            self.thread = GenericThread(self.do_scan)
            self.thread.finished.connect(self.save_settings_to_database)
            self.thread.finished.connect(self.continue_scan)
            self.thread.start()
            self.scan_no += 1
        else:
            self.abort_scan = False
            self.enable_run_button(scan=self.model.data.scanDict['parameter_scan'])
            self.reset_progress_bar_timer()
            self.update_widgets_with_values(self.scan_parameter, self.scan_basevalue)
            self.update_directory_widget()

    def check_scan_parameters(self):
        try:
            scan_start = float(self.model.data.scanDict['parameter_scan_from_value'])
            scan_end = float(self.model.data.scanDict['parameter_scan_to_value'])
            scan_step_size = float(self.model.data.scanDict['parameter_scan_step_size'])
            scan_range = np.arange(scan_start, scan_end + scan_step_size, scan_step_size)
            if len(scan_range) > 0:
                return True
            return False
        except ValueError:
            return False

    def app_sequence(self):
        if self.model.data.scanDict['parameter_scan']:
            if self.check_scan_parameters():
                self.setup_scan()
            else:
                print('Error in scan parameters - aborting!')
        else:
            self.thread = GenericThread(self.do_scan)
            self.thread.finished.connect(self.enable_run_button)
            self.thread.finished.connect(self.update_directory_widget)
            self.thread.finished.connect(lambda:self.save_settings_to_database(self.view.autoPlotCheckbox.isChecked()))
            self.thread.start()
        return

    def save_settings_to_database(self, plot=False):
        if self.tracking_success:
            self.model.save_settings_to_database(self.model.yaml, self.model.directoryname)
            self.update_runs_widget(plot=plot, id=self.model.directoryname)

    def update_directory_widget(self):
        dirname = self.model.get_directory_name()
        self.update_widgets_with_values('runs:directory', dirname)

    def update_runs_widget(self, plot=False, id=None):
        dirname = self.model.get_directory_name()
        # settings = self.model.import_yaml_from_server()
        # print('Adding row - ', str(self.model.run_number), dirname)
        self.populate_run_parameters_table()
        if plot:
            self.enable_plot_on_id(id)

    def reset_progress_bar_timer(self):
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.view.progressBar.reset)
        self.timer.start()

    def run_astra(self):
        self.disable_run_button(scan=self.model.data.scanDict['parameter_scan'])
        self.app_sequence()

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
