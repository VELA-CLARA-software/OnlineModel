try:
    from PyQt4.QtCore import *
    from PyQt4.QtGui import *
except:
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *
from copy import copy,deepcopy
from decimal import Decimal
import run_parameters_parser as yaml_parser
import sys, os, math, epics, scipy.constants, numpy
import json, requests, datetime, time
import collections
import numpy as np

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

    def __init__(self, app, view, model):
        super(RunParameterController, self).__init__()
        self.my_name = 'controller'
        self.app = app
        self.model = model
        self.view = view
        self.runParameterLayouts = [
                               self.view.s02_parameter_groupbox,
                               self.view.c2v_parameter_groupbox,
                               self.view.vela_parameter_groupbox,
                               self.view.ba1_parameter_groupbox,
                               self.view.injector_parameter_groupbox,
                               self.view.simulation_parameter_groupbox,
                               self.view.scan_groupBox,
                               self.view.directory_groupBox
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
        self.view.runButton.clicked.connect(lambda: self.export_parameter_values_to_yaml_file(auto=True))
        self.view.loadSettingsButton.clicked.connect(self.load_settings_from_directory)
        self.view.directory.textChanged[str].connect(self.check_load_settings_button)
        self.view.directory.textChanged[str].emit(self.view.directory.text())
        self.abort_scan = False

    def connect_auto_load_settings(self, state):
        if state:
            self.view.directory.textChanged[str].connect(self.load_settings_from_directory)
        else:
            try:
                self.view.directory.textChanged[str].disconnect(self.load_settings_from_directory)
            except:
                pass

    def check_load_settings_button(self, text):
        if os.path.isfile(text + '/settings.yaml'):
            self.view.loadSettingsButton.setEnabled(True)
        else:
            self.view.loadSettingsButton.setEnabled(False)

    def load_settings_from_directory(self):
        if os.path.isfile(self.model.data.parameterDict['simulation']['directory'] + '/settings.yaml'):
            self.import_parameter_values_from_yaml_file(self.model.data.parameterDict['simulation']['directory'] + '/settings.yaml')

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
        for i in range(2,7):
            combo.addItem(str(2**(3*i)), i)
        combo.setCurrentIndex(1)

    def split_accessible_name(self, aname):
        if len((aname.split(':'))) == 3:
            dictname, pv, param = map(str, aname.split(':'))
        else:
            param = None
            dictname, pv = map(str, aname.split(':'))
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
            self.model.data.parameterDict[dictname].update({pv: value})
        else:
            try:
                self.model.data.parameterDict[dictname][pv].update({param: value})
            except:
                print('Error ', dictname, pv, param, value)

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
                    scannableParameterDict[' - '.join(list(key.split(':'))[1:])] = key
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
                if type(widget) is QDoubleSpinBox:
                    widget.setValue(float(value))
                if type(widget) is QSpinBox:
                    widget.setValue(int(value))
                if type(widget) is QCheckBox:
                    if value is True:
                        widget.setChecked(True)
                    else:
                        widget.setChecked(False)
                if type(widget) is QComboBox:
                    index = widget.findText(value)
                    if index == -1:
                        index = widget.findData(value)
                    widget.setCurrentIndex(index)

    ## Need to port this to the unified controller
    @pyqtSlot()
    def import_parameter_values_from_yaml_file(self, filename=None):
        if filename is None:
            dialog = QFileDialog()
            filename = QFileDialog.getOpenFileName(dialog, caption='Open file',
                                                         directory=self.model.data.parameterDict['simulation']['directory'],
                                                         filter="YAML files (*.YAML *.YML *.yaml *.yml)")
        filename = filename[0] if isinstance(filename,tuple) else filename
        filename = str(filename)
        if not filename == '' and not filename is None and (filename[-4:].lower() == '.yml' or filename[-5:].lower() == '.yaml'):
            loaded_parameter_dict = yaml_parser.parse_parameter_input_file(filename)
            for (parameter, value) in loaded_parameter_dict.items():
                    self.update_widgets_with_values(parameter, value)
        else:
            print('Failed to import, please provide a filename')

    def convert_data_types(self, export_dict={}, data_dict={}, keyname=None):
        if keyname is not None:
            export_dict[keyname] = dict()
            edict = export_dict[keyname]
        else:
            edict = export_dict
        for key, value in data_dict.items():
            if isinstance(value, (dict, collections.OrderedDict)) and not key == 'sub_elements':
                subdict = self.convert_data_types({}, value)
                edict.update({key:subdict})
            else:
                if not key == 'sub_elements':
                    # value = self.model.data.Framework.convert_numpy_types(value)
                    edict.update({key:value})
        return export_dict

    def create_subdirectory(self, dir):
        if not os.path.exists(dir):
            os.makedirs(dir, exist_ok=True)

    def export_parameter_values_to_yaml_file(self, auto=False):
        export_dict = dict()
        data_dicts = ['generator', 'INJ', 'S02', 'C2V', 'EBT', 'BA1', 'simulation']
        if self.model.data.scanDict['parameter_scan']:
            if not auto:
                dialog = QFileDialog()
                directory = QFileDialog.getExistingDirectory(dialog,"Select Directory")
                filename =  '/scan_settings.yaml'
            else:
                directory = self.model.data.parameterDict['simulation']['directory']
                filename =  '/scan_settings.yaml'
            data_dicts.append('scan')
        else:
            if not auto:
                dialog = QFileDialog()
                filename, _filter = QFileDialog.getSaveFileNameAndFilter(dialog, caption='Save File', directory='c:\\',
                                                                     filter="YAML Files (*.YAML *.YML *.yaml *.yml")
                filename = filename[0] if isinstance(filename,tuple) else filename
                dirctory, filename = os.path.split(filename)
            else:
                directory = self.model.data.parameterDict['simulation']['directory']
                filename = 'settings.yaml'
        if not filename == "":
            print('directory = ', directory, '   filename = ', filename, '\njoin = ', str(os.path.relpath(directory + '/' + filename)))
            self.create_subdirectory(directory)
            for n in data_dicts:
                export_dict = self.convert_data_types(export_dict, self.model.data.parameterDict[n], n)
            yaml_parser.write_parameter_output_file(str(os.path.relpath(directory + '/' + filename)), export_dict)
        else:
            print( 'Failed to export, please provide a filename.')

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
        if not scan:
            self.view.runButton.setEnabled(False)
        else:
            self.view.runButton.clicked.disconnect()
            self.view.runButton.setText('Abort')
            self.view.runButton.clicked.connect(self.abort_ongoing_scan)


    def read_from_epics(self, time_from=None, time_to=None):
        for l in self.model.data.lattices:
            self.model.data.read_values_from_epics(self.model.data.parameterDict[l], lattice=True)
            for key, value in self.model.data.parameterDict[l].items():
                if value['type'] == "quadrupole":
                    self.update_widgets_with_values(l + ':' + key + ':k1l', value['k1l'])
                if value['type'] == "solenoid":
                    self.update_widgets_with_values(l + ':' + key + ':field_amplitude', value['field_amplitude'])
                if value['type'] == "cavity":
                    self.update_widgets_with_values(l + ':' + key + ':phase', value['phase'])
                    self.update_widgets_with_values(l + ':' + key + ':field_amplitude', value['field_amplitude'])
        self.model.data.read_values_from_epics(self.model.data.parameterDict['generator'], lattice=False)
        for key, value in self.model.data.parameterDict['generator'].items():
            if key == "charge":
                self.update_widgets_with_values('generator:' + key + ':value', value['value'])
            # self.update_widget_from_dict(key)

        return

    def abort_ongoing_scan(self):
        self.abort_scan = True

    def enable_run_button(self, scan=False):
        self.view.runButton.setText('Track')
        self.view.runButton.clicked.disconnect()
        if not scan:
            self.view.runButton.setEnabled(True)
        else:
            pass
        self.view.runButton.clicked.connect(self.run_astra)
        self.view.runButton.clicked.connect(lambda: self.export_parameter_values_to_yaml_file(auto=True))
        return

    def toggle_finished_tracking(self):
        if self.finished_tracking:
            self.finished_tracking = False
        else:
            self.finished_tracking = True

    def setup_scan(self):
        self.export_parameter_values_to_yaml_file(auto=True)
        try:
            scan_start = float(self.model.data.scanDict['parameter_scan_from_value'])
            scan_end = float(self.model.data.scanDict['parameter_scan_to_value'])
            scan_step_size = float(self.model.data.scanDict['parameter_scan_step_size'])
            scan_range = np.arange(scan_start, scan_end + scan_step_size, scan_step_size)
            self.view.progressBar.setRange(0,len(scan_range))
        except ValueError:
            print("Enter a numerical value to conduct a scan")
        self.scan_parameter = self.model.data.scanDict['parameter']
        self.scan_basedir = str(self.model.data.parameterDict['simulation']['directory'])
        self.scan_basevalue = self.get_widget_value(self.get_object_by_accessible_name(self.scan_parameter))
        dictname, pv, param = self.split_accessible_name(self.scan_parameter)
        self.scan_range = np.arange(scan_start, scan_end + scan_step_size, scan_step_size)
        self.scan_no = 0
        self.continue_scan()

    def do_scan(self):
        self.model.run_script()

    def continue_scan(self):
        if not self.abort_scan and self.scan_no < len(self.scan_range):
            self.view.progressBar.setValue(self.scan_no+1)
            self.scan_progress = self.scan_no+1
            current_scan_value = round(self.scan_range[self.scan_no], 5)
            print('Scanning['+str(self.scan_no)+']: Setting ', self.scan_parameter, ' to ', current_scan_value)
            self.update_widgets_with_values(self.scan_parameter, current_scan_value)
            dictname, pv, param = self.split_accessible_name(self.scan_parameter)
            subdir = (self.scan_basedir + '/' + pv + '_' + str(current_scan_value)).replace('//','/')
            self.update_widgets_with_values('simulation:directory', subdir)
            self.thread = GenericThread(self.do_scan)
            self.thread.finished.connect(self.continue_scan)
            self.thread.start()
            self.scan_no += 1
        else:
            self.abort_scan = False
            self.enable_run_button(scan=self.model.data.scanDict['parameter_scan'])
            self.reset_progress_bar_timer()
            self.update_widgets_with_values(self.scan_parameter, self.scan_basevalue)
            self.update_widgets_with_values('simulation:directory', self.scan_basedir)

    def app_sequence(self):
        if self.model.data.scanDict['parameter_scan']:
            self.setup_scan()
        else:
            self.thread = GenericThread(self.do_scan)
            self.thread.finished.connect(self.enable_run_button)
            self.thread.start()
        return

    def reset_progress_bar_timer(self):
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.view.progressBar.reset)
        self.timer.start()

    def run_astra(self):
        self.disable_run_button(scan=self.model.data.scanDict['parameter_scan'])
        self.app_sequence()
