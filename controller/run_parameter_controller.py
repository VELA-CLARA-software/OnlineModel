from PyQt4.QtCore import *
from PyQt4.QtGui import *
from copy import copy,deepcopy
from decimal import Decimal
import run_parameters_parser as yaml_parser
import sys, os, time
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
                               self.view.directory_groupBox,
                               ]
        self.formLayoutList = [formLayout for layout in self.runParameterLayouts for
                          formLayout in layout.findChildren((QFormLayout,QGridLayout))]
        #self.model.data.self.model.data.runParameterDict = self.initialize_run_parameter_data()
        self.update_macro_particle_combo()
        self.initialize_run_parameter_data()
        self.model.data.scannableParametersDict = self.get_scannable_parameters_dict()
        self.populate_scan_combo_box()
        self.view.parameter_scan.stateChanged.connect(lambda: self.toggle_scan_parameters_state(self.view.parameter_scan))
        self.view.runButton.clicked.connect(self.run_astra)
        self.view.runButton.clicked.connect(lambda: self.export_parameter_values_to_yaml_file(auto=True))
        self.value_to_be_checked = 0
        self.sm = signalling_monitor(self.model, 'scan_progress')
        self.sm.valueChanged.connect(self.view.progressBar.setValue)

    def update_macro_particle_combo(self):
        combo = self.view.macro_particle
        for i in range(2,7):
            combo.addItem(str(2**(3*i)), i)
        combo.setCurrentIndex(1)

    @pyqtSlot()
    def update_value_in_dict(self):
        widget = self.sender()
        dictname = (widget.accessibleName().split(':'))[0]
        if len((widget.accessibleName().split(':'))) == 3:
            dictname, pv, param = map(str, widget.accessibleName().split(':'))
        else:
            param = None
            dictname, pv = map(str, widget.accessibleName().split(':'))
        if type(widget) is QLineEdit:
            try:
                value = float(widget.text())
            except:
                value = str(widget.text())
        elif type(widget) is QDoubleSpinBox:
            value = round(float(widget.value()), widget.decimals())
        elif type(widget) is QCheckBox:
            value = True if widget.isChecked() else False
        elif type(widget) is QComboBox:
            value = widget.itemData(widget.currentIndex())
            if value == '' or value is None:
                value = str(widget.currentText())
            if isinstance(value, QVariant):
                value = value.toString()
            value = str(value)
        if param is None:
            self.model.data.parameterDict[dictname].update({pv: value})
        else:
            self.model.data.parameterDict[dictname][pv].update({param: value})

    def initialize_run_parameter_data(self):
        self.scannableParameters = []
        for layout in self.formLayoutList:
            childCount = layout.count()
            for child in range(0,childCount):
                widget = layout.itemAt(child).widget()
                if type(widget) is QLineEdit:
                    widget.textChanged.connect(self.update_value_in_dict)
                    widget.textChanged.emit(widget.placeholderText())
                if type(widget) is QDoubleSpinBox:
                    widget.valueChanged.connect(self.update_value_in_dict)
                    widget.valueChanged.emit(widget.value())
                    self.scannableParameters.append(str(widget.accessibleName()))
                if type(widget) is QCheckBox:
                    value = True if widget.isChecked() else False
                    widget.stateChanged.connect(self.update_value_in_dict)
                    widget.stateChanged.emit(widget.isChecked())
                if type(widget) is QComboBox:
                    widget.currentIndexChanged.connect(self.update_value_in_dict)
                    widget.currentIndexChanged.emit(widget.currentIndex())
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
        if len((aname.split(':'))) == 3:
            dictname, pv, param = map(str, aname.split(':'))
        else:
            param = None
            dictname, pv = map(str, aname.split(':'))
        if param is None:
            value = self.model.data.parameterDict[dictname][pv]
        else:
            value = self.model.data.parameterDict[dictname][pv][param]
        self.update_widgets_with_values(aname, value)

    def get_object_by_accessible_name(self, aname):
        for layout in self.formLayoutList:
            childCount = layout.count()
            for child in range(0,childCount):
                widget = layout.itemAt(child).widget()
                try:
                    if widget.accessibleName() == aname:
                        return widget
                except:
                    pass
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
                    widget.setValue(value)
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
    def import_parameter_values_from_yaml_file(self):
        dialog = QFileDialog()
        filename = QFileDialog.getOpenFileName(dialog, caption='Open file',
                                                     directory=self.model.data.parameterDict['simulation']['directory'],
                                                     filter="YAML files (*.YAML *.YML *.yaml *.yml)")
        if not filename == '':
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

    @pyqtSlot()
    def export_parameter_values_to_yaml_file(self, auto=False):
        export_dict = dict()
        data_dicts = ['generator', 'lattice', 'simulation']
        if self.model.data.scanDict['parameter_scan']:
            if not auto:
                dialog = QFileDialog()
                directory = QFileDialog.getExistingDirectory(dialog,"Select Directory")
                filename =  directory + '/scan_settings.yaml'
            else:
                directory = self.model.data.parameterDict['simulation']['directory']
                filename =  directory + '/scan/scan_settings.yaml'
            data_dicts.append('scan')
        else:
            if not auto:
                dialog = QFileDialog()
                filename, _filter = QFileDialog.getSaveFileNameAndFilter(dialog, caption='Save File', directory='c:\\',
                                                                     filter="YAML Files (*.YAML *.YML *.yaml *.yml")
            else:
                filename = self.model.data.parameterDict['simulation']['directory'] + '/settings.yaml'
        if not filename == "":
            for n in data_dicts:
                export_dict = self.convert_data_types(export_dict, self.model.data.parameterDict[n], n)
            yaml_parser.write_parameter_output_file(str(filename), export_dict)
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

    def disable_run_button(self):
        self.view.runButton.setEnabled(False)
        return

    def enable_run_button(self):
        self.view.runButton.setEnabled(True)
        return

    def app_sequence(self):
        self.model.run_script()
        return

    def reset_progress_bar_timer(self):
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.view.progressBar.reset)
        self.timer.start()

    def run_astra(self):
        if self.model.data.scanDict['parameter_scan']:
            scan_start = float(self.model.data.scanDict['parameter_scan_from_value'])
            scan_end = float(self.model.data.scanDict['parameter_scan_to_value'])
            scan_step_size = float(self.model.data.scanDict['parameter_scan_step_size'])
            scan_range = np.arange(scan_start, scan_end + scan_step_size, scan_step_size)
            self.view.progressBar.setRange(0,len(scan_range))
        self.disable_run_button()
        self.sm.start()
        self.thread = GenericThread(self.app_sequence)
        self.thread.finished.connect(self.enable_run_button)
        self.thread.finished.connect(self.sm.stop)
        self.thread.finished.connect(self.reset_progress_bar_timer)
        self.thread.start()



    # @pyqtSlot()
    # def handle_existent_file(self):
        # print('Directory '+self.model.data.self.model.data.runParameterDict['directory_line_edit'] + 'already exists')
