from PyQt4.QtCore import *
from PyQt4.QtGui import *
from copy import copy,deepcopy
from decimal import Decimal
import run_parameters_parser as yaml_parser
import sys, os, math, epics, scipy.constants, numpy
import collections

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
        #self.model.data.self.model.data.runParameterDict = self.initialize_run_parameter_data()
        self.initialize_run_parameter_data()
        self.model.data.scannableParametersDict = self.get_scannable_parameters_dict()
        self.populate_scan_combo_box()
        self.view.parameter_scan.stateChanged.connect(lambda: self.toggle_scan_parameters_state(self.view.parameter_scan))
        self.view.runButton.clicked.connect(self.run_astra)
        self.view.runButton.clicked.connect(lambda: self.export_parameter_values_to_yaml_file(auto=True))
        self.update_macro_particle_combo()

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
            if isinstance(value, QVariant):
                value = value.toString()
            value = str(value)
            if value is '':
                value = str(widget.currentText())
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
                    widget.currentIndexChanged[str].connect(self.update_value_in_dict)
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

    def set_spinbox_text_by_name(self, name, value):
        formLayoutList = [formLayout for layout in self.runParameterLayouts for formLayout in layout.findChildren(QFormLayout)]
        for layout in formLayoutList:
            childCount = layout.count()
            for childIndex in range(0, childCount):
                widget = layout.itemAt(childIndex).widget()
                if type(widget) == QDoubleSpinBox and name == widget.accessibleName():
                    print(widget.accessibleName())
                    widget.setValue(value)

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

    def strip_text_before(self, string, condition):
        sep = condition
        rest = string.split(sep, 1)[0]
        return rest

    def strip_text_after(self, string, condition):
        sep = condition
        rest = string.split(sep, 1)[1]
        return rest

    def read_values_from_epics(self):
        self.update_mag_field_coefficients()
        gun_cavity_length = self.model.data.parameterDict['lattice']['CLA-LRG1-GUN-CAV']['length']
        gun_klystron_power = 1
        gun_phase = 1
        gun_pulse_length = 1
        l01_cavity_length = self.model.data.parameterDict['lattice']['CLA-L01-CAV']['length']
        linac_klystron_power = 1
        linac_phase = 1
        linac_pulse_length = 1
        fudge = 0
        gun_energy_gain = self.get_energy_from_rf(gun_klystron_power, gun_phase, gun_pulse_length)
        self.model.data.parameterDict['lattice']['CLA-LRG1-GUN-CAV']['field_amplitude'] = gun_energy_gain / gun_cavity_length
        self.model.data.parameterDict['lattice']['CLA-LRG1-GUN-CAV'].update({'energy_gain': gun_energy_gain})
        self.model.data.parameterDict['lattice']['CLA-LRG1-GUN-CAV']['phase'] = gun_phase
        self.model.data.parameterDict['lattice']['CLA-LRG1-GUN-CAV'].update({'pulse_length': gun_pulse_length})
        self.set_spinbox_text_by_name("lattice:"+"CLA-LRG1-GUN-CAV"+":field_amplitude", gun_energy_gain / gun_cavity_length)
        self.set_spinbox_text_by_name("lattice:"+"CLA-LRG1-GUN-CAV"+":phase", gun_phase)
        linac_energy_gain = self.get_energy_from_rf(linac_klystron_power, linac_phase, linac_pulse_length)
        self.model.data.parameterDict['lattice']['CLA-L01-CAV']['field_amplitude'] = linac_energy_gain / l01_cavity_length
        self.model.data.parameterDict['lattice']['CLA-L01-CAV'].update({'energy_gain': linac_energy_gain})
        self.model.data.parameterDict['lattice']['CLA-L01-CAV']['phase'] = linac_phase
        self.model.data.parameterDict['lattice']['CLA-L01-CAV'].update({'pulse_length': linac_pulse_length})
        self.set_spinbox_text_by_name("lattice:" + 'CLA-L01-CAV' + ":field_amplitude", linac_energy_gain / l01_cavity_length)
        self.set_spinbox_text_by_name("lattice:" + 'CLA-L01-CAV' + ":phase", linac_phase)
        total_energy_gain = gun_energy_gain + linac_energy_gain + fudge
        speed_of_light = scipy.constants.speed_of_light / 1e6
        for key, value in self.model.data.parameterDict['lattice'].items():
            if value['type'] == 'quadrupole':
                current = 1 #epics.caget(name+"SETI")
                coeffs = numpy.append(value['field_integral_coefficients'][:-1], value['field_integral_coefficients'][-1])
                int_strength = numpy.polyval(coeffs, current)
                effect = speed_of_light * int_strength / total_energy_gain
                self.set_spinbox_text_by_name("lattice:"+key+":k1l", effect / value['magnetic_length'])
                # value['k1l'] = effect / value['magnetic_length']
            elif value['type'] == 'solenoid':
                current = 1 #epics.caget(name+"SETI")
                sign = numpy.copysign(1, current)
                coeffs = numpy.append(value['field_integral_coefficients'][-4:-1] * int(sign), value['field_integral_coefficients'][-1])
                int_strength = numpy.polyval(coeffs, current)
                effect = int_strength / value['magnetic_length']
                self.set_spinbox_text_by_name("lattice:"+key+":field_amplitude", effect / value['magnetic_length'])
                # value['field_amplitude'] = effect / value['magnetic_length']
        self.set_spinbox_text_by_name("generator:"+"spot_size"+":value", 1)
        self.set_spinbox_text_by_name("generator:"+"charge"+":value", 1)

    def get_energy_from_rf(self, klystron_power, phase, pulse_length):
        bestcase = 0.407615 + 1.94185 * (((1 - math.exp((-1.54427 * 10 ** 6 * pulse_length * 10 ** -6))) * (0.0331869 + 6.05422 * 10 ** -7 * klystron_power * 10 ** 6)) * numpy.cos(phase)) ** 0.5
        worstcase = 0.377 + 1.81689 * (((1 - math.exp((-1.54427 * 10 ** 6 * pulse_length * 10 ** -6))) * (0.0331869 + 6.05422 * 10 ** -7 * klystron_power * 10 ** 6)) * numpy.cos(phase)) ** 0.5
        return numpy.mean([bestcase, worstcase])

    def update_mag_field_coefficients(self):
        s02ficq1 = [-2.23133410405682E-10, 4.5196171252132E-08, -3.46208258004659E-06, 1.11195870210961E-04, 2.38129337415767E-02, 9.81229429460256E-03]
        s02ficq2 = [-4.69068497199892E-10, 7.81236692669882E-08, -4.99557108021749E-06, 1.39687166906618E-04, 2.32819099224878E-02, 9.77695097574923E-03]
        s02ficq3 = [-4.01132756980213E-10, 7.04774652367448E-08, -4.7303680012511E-06, 1.37571730391246E-04, 2.33327839789932E-02, 9.49568371388574E-03]
        s02ficq4 = [-3.12868198002574E-10, 5.87771428279647E-08, -4.18748562338666E-06, 1.27524427731924E-04, 2.34218216296292E-02, 9.38588316008555E-03]
        c2vficq1 = [-1.30185900474931E-11, 5.70352698264348E-09, -9.08937880373639E-07, 6.03053164909332E-05, 0.014739040805921, 1.37593271780352E-02]
        c2vficq2 = [-1.30779403854705E-11, 5.72293796261772E-09, -9.08645007418186E-07, 5.97762384752619E-05, 1.47596073775721E-02, 1.58516912403471E-02]
        c2vficq3 = [-1.31651924239548E-11, 5.76805215137824E-09, -9.16843633799561E-07, 6.036266595182E-05, 1.47634437187611E-02, 0.013343693771224]
        ebtficq7 = [-1.51802828278694E-05, 0.000208236492203741, 0.102224127676636, 0.00205656183129602]
        ebtficq8 = [-3.06357099595939E-05, 0.000442533546326552, 0.101577009522434, 0.00146589509380893]
        ebtficq9 = [0.111939163037871, -0.00132252769474545]
        ebtficq10 = [0.111966157109812, -0.00170732356716569]
        ebtficq11 = [0.112072763436341, -0.00182025848896622]
        ebtficq15 = [0.111954754, -0.001381788]
        ba1ficq1 = [1.59491, -0.01760]
        ba1ficq2 = [1.59214, -0.01508]
        ba1ficq3 = [1.59020, -0.01823]
        ba1ficq4 = [1.58881, -0.01033]
        ba1ficq5 = [1.59298, -0.02111]
        ba1ficq6 = [1.58624, 0.00451]
        ba1ficq7 = [0.36799, 0.00144]
        lrgbsolfic = [0.000513431, -1.27695e-7, 1.61655e-10, -0.032733798, -4.29885e-06, 2.28967e-08, 0.001833327,
                      -2.5354e-06, -1.04715e-09, -1.61177e-12, -2.94837e-05, 2.13938e-07, -0.003957362, 0.246073139,
                      -4.393602393, 0.0]
        lrgsolfic = [2.17321571, -0.858179277, 0.172127130, -0.0171033399, 6.70371530e-04,  -3.53922e-08, 1.53138e-05, 0.167819191, 0.0]
        l01sol1fic = [0.911580969, -0.0374385376, 0.00106926073, -1.64644381e-05, 1.01769629e-07,    0,    0,    0.37651102,  0.12171419]
        l01sol2fic = [0.847688880, -0.0653499119, 0.00243270133, -4.29020066e-05, 2.87019853e-07,    0,    0,    0.37651102,  0.12171419]
        s02mlq1 = 128.68478212775
        s02mlq2 = 126.817287248819
        s02mlq3 = 127.241994829126
        s02mlq4 = 127.421664936758
        c2vmlq1 = 121.567272525393
        c2vmlq2 = 121.511900610076
        c2vmlq3 = 121.550749828396
        ebtmlq7 = 125.299909233924
        ebtmlq8 = 125.27558356645
        ebtmlq9 = 70.4236023746139
        ebtmlq10 = 70.4236023746139
        ebtmlq11 = 70.4236023746139
        ebtmlq15 = 70.4236023746139
        ba1mlq1 = 70.4236023746139
        ba1mlq2 = 70.4236023746139
        ba1mlq3 = 70.4236023746139
        ba1mlq4 = 70.4236023746139
        ba1mlq5 = 70.4236023746139
        ba1mlq6 = 70.4236023746139
        ba1mlq7 = 70.4236023746139
        lrgbsolml = 12.5
        lrgsolml = 139.50
        l01sol1ml = 726.91820512820505
        l01sol2ml = 726.91820512820505
        self.model.data.parameterDict['lattice']['CLA-S02-MAG-QUAD-01'].update({'field_integral_coefficients':s02ficq1})
        self.model.data.parameterDict['lattice']['CLA-S02-MAG-QUAD-02'].update({'field_integral_coefficients':s02ficq2})
        self.model.data.parameterDict['lattice']['CLA-S02-MAG-QUAD-03'].update({'field_integral_coefficients':s02ficq3})
        self.model.data.parameterDict['lattice']['CLA-S02-MAG-QUAD-04'].update({'field_integral_coefficients':s02ficq4})
        self.model.data.parameterDict['lattice']['CLA-C2V-MAG-QUAD-01'].update({'field_integral_coefficients':c2vficq1})
        self.model.data.parameterDict['lattice']['CLA-C2V-MAG-QUAD-02'].update({'field_integral_coefficients':c2vficq2})
        self.model.data.parameterDict['lattice']['CLA-C2V-MAG-QUAD-03'].update({'field_integral_coefficients':c2vficq3})
        self.model.data.parameterDict['lattice']['EBT-INJ-MAG-QUAD-07'].update({'field_integral_coefficients':ebtficq7})
        self.model.data.parameterDict['lattice']['EBT-INJ-MAG-QUAD-08'].update({'field_integral_coefficients':ebtficq8})
        self.model.data.parameterDict['lattice']['EBT-INJ-MAG-QUAD-09'].update({'field_integral_coefficients':ebtficq9})
        self.model.data.parameterDict['lattice']['EBT-INJ-MAG-QUAD-10'].update({'field_integral_coefficients':ebtficq10})
        self.model.data.parameterDict['lattice']['EBT-INJ-MAG-QUAD-11'].update({'field_integral_coefficients':ebtficq11})
        self.model.data.parameterDict['lattice']['EBT-INJ-MAG-QUAD-15'].update({'field_integral_coefficients':ebtficq15})
        self.model.data.parameterDict['lattice']['EBT-BA1-MAG-QUAD-01'].update({'field_integral_coefficients':ba1ficq1})
        self.model.data.parameterDict['lattice']['EBT-BA1-MAG-QUAD-02'].update({'field_integral_coefficients':ba1ficq2})
        self.model.data.parameterDict['lattice']['EBT-BA1-MAG-QUAD-03'].update({'field_integral_coefficients':ba1ficq3})
        self.model.data.parameterDict['lattice']['EBT-BA1-MAG-QUAD-04'].update({'field_integral_coefficients':ba1ficq4})
        self.model.data.parameterDict['lattice']['EBT-BA1-MAG-QUAD-05'].update({'field_integral_coefficients':ba1ficq5})
        self.model.data.parameterDict['lattice']['EBT-BA1-MAG-QUAD-06'].update({'field_integral_coefficients':ba1ficq6})
        self.model.data.parameterDict['lattice']['EBT-BA1-MAG-QUAD-07'].update({'field_integral_coefficients':ba1ficq7})
        self.model.data.parameterDict['lattice']['CLA-LRG1-GUN-SOL'].update({'field_integral_coefficients':lrgbsolfic})
        self.model.data.parameterDict['lattice']['CLA-L01-CAV-SOL-01'].update({'field_integral_coefficients':l01sol1fic})
        self.model.data.parameterDict['lattice']['CLA-L01-CAV-SOL-02'].update({'field_integral_coefficients':l01sol2fic})
        self.model.data.parameterDict['lattice']['CLA-S02-MAG-QUAD-01'].update({'magnetic_length': s02mlq1})
        self.model.data.parameterDict['lattice']['CLA-S02-MAG-QUAD-02'].update({'magnetic_length': s02mlq2})
        self.model.data.parameterDict['lattice']['CLA-S02-MAG-QUAD-03'].update({'magnetic_length': s02mlq3})
        self.model.data.parameterDict['lattice']['CLA-S02-MAG-QUAD-04'].update({'magnetic_length': s02mlq4})
        self.model.data.parameterDict['lattice']['CLA-C2V-MAG-QUAD-01'].update({'magnetic_length': c2vmlq1})
        self.model.data.parameterDict['lattice']['CLA-C2V-MAG-QUAD-02'].update({'magnetic_length': c2vmlq2})
        self.model.data.parameterDict['lattice']['CLA-C2V-MAG-QUAD-03'].update({'magnetic_length': c2vmlq3})
        self.model.data.parameterDict['lattice']['EBT-INJ-MAG-QUAD-07'].update({'magnetic_length': ebtmlq7})
        self.model.data.parameterDict['lattice']['EBT-INJ-MAG-QUAD-08'].update({'magnetic_length': ebtmlq8})
        self.model.data.parameterDict['lattice']['EBT-INJ-MAG-QUAD-09'].update({'magnetic_length': ebtmlq9})
        self.model.data.parameterDict['lattice']['EBT-INJ-MAG-QUAD-10'].update({'magnetic_length': ebtmlq10})
        self.model.data.parameterDict['lattice']['EBT-INJ-MAG-QUAD-11'].update({'magnetic_length': ebtmlq11})
        self.model.data.parameterDict['lattice']['EBT-INJ-MAG-QUAD-15'].update({'magnetic_length': ebtmlq15})
        self.model.data.parameterDict['lattice']['EBT-BA1-MAG-QUAD-01'].update({'magnetic_length': ba1mlq1})
        self.model.data.parameterDict['lattice']['EBT-BA1-MAG-QUAD-02'].update({'magnetic_length': ba1mlq2})
        self.model.data.parameterDict['lattice']['EBT-BA1-MAG-QUAD-03'].update({'magnetic_length': ba1mlq3})
        self.model.data.parameterDict['lattice']['EBT-BA1-MAG-QUAD-04'].update({'magnetic_length': ba1mlq4})
        self.model.data.parameterDict['lattice']['EBT-BA1-MAG-QUAD-05'].update({'magnetic_length': ba1mlq5})
        self.model.data.parameterDict['lattice']['EBT-BA1-MAG-QUAD-06'].update({'magnetic_length': ba1mlq6})
        self.model.data.parameterDict['lattice']['EBT-BA1-MAG-QUAD-07'].update({'magnetic_length': ba1mlq7})
        self.model.data.parameterDict['lattice']['CLA-LRG1-GUN-SOL'].update({'magnetic_length': lrgbsolml})
        self.model.data.parameterDict['lattice']['CLA-L01-CAV-SOL-01'].update({'magnetic_length': l01sol1ml})
        self.model.data.parameterDict['lattice']['CLA-L01-CAV-SOL-02'].update({'magnetic_length': l01sol2ml})
    # def run_thread(self, func):
        # self.thread = GenericThread(func)
        # self.thread.finished.connect(self.enable_run_button)

    def disable_run_button(self):
        self.view.runButton.setEnabled(False)
        return

    def enable_run_button(self):
        self.view.runButton.setEnabled(True)
        return

    def app_sequence(self):
        #self.collect_parameters()
        #self.collect_scan_parameters()
        # self.model.ssh_to_server()
        # self.model.create_subdirectory()
        # if self.model.path_exists:
            # self.thread.stop()
            # self.thread.finished.connect(self.enable_run_button())
            # self.thread.signal.connect(self.handle_existent_file)

        # else:
            # self.thread._stopped = False
        self.model.run_script()
        return

    def run_astra(self):
        self.read_values_from_epics()
        # self.disable_run_button()
        # self.app_sequence()
        # self.enable_run_button()
        #self.run_thread(self.app_sequence)
        #self.thread.start()


    # @pyqtSlot()
    # def handle_existent_file(self):
        # print('Directory '+self.model.data.self.model.data.runParameterDict['directory_line_edit'] + 'already exists')
