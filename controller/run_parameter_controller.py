from PyQt4.QtCore import *
from PyQt4.QtGui import *
from copy import copy,deepcopy
from decimal import Decimal
import run_parameters_parser as yaml_parser
import sys, os
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
        self.runParameterLayouts = [self.view.simulation_parameter_groupbox,
                               self.view.injector_parameter_groupbox,
                               self.view.s02_parameter_groupbox,
                               self.view.c2v_parameter_groupbox,
                               self.view.vela_parameter_groupbox,
                               self.view.ba1_parameter_groupbox,
                               ]
        #self.model.data.self.model.data.runParameterDict = self.initialize_run_parameter_data()
        self.initialize_run_parameter_data()
        self.model.data.scannableParametersDict = self.get_scannable_parameters_dict()
        self.populate_scan_combo_box()
        self.model.data.parameterScanDict = self.initialize_parameter_scan_data()
        self.model.data.directoryDict = self.initialize_directory_data()
        self.view.parameter_scan.stateChanged.connect(self.toggle_scan_parameters_state)
        self.view.runButton.clicked.connect(self.run_astra)

    @pyqtSlot()
    def update_value_in_run_parameter_data(self):
        widget = self.sender()
        if type(widget) is QLineEdit:
            # print widget.objectName(), widget.accessibleName(), widget.text()
            #self.model.data.self.model.data.runParameterDict.update({str(widget.accessibleName()) : str(widget.text())})
            if str(self.strip_text_before(widget.accessibleName(), ':')) in self.model.data.runParameterDict.keys():
                if str(widget.text()) == '':
                    if self.model.data.runParameterDict[str(self.strip_text_before(widget.accessibleName(), ':'))][
                        'type'] == 'quadrupole':
                        self.model.data.runParameterDict[str(widget.accessibleName())].update(
                            {'k1l': float(str(widget.placeholderText()))})
                    elif self.model.data.runParameterDict[str(self.strip_text_before(widget.accessibleName(), ':'))][
                        'type'] == 'cavity':
                        if str(self.strip_text_after(widget.accessibleName(), ':')) == 'AMP':
                            self.model.data.runParameterDict[str(self.strip_text_before(widget.accessibleName(), ':'))].update(
                                {'field_amplitude': 1e6*float(str(widget.placeholderText()))})
                        elif str(self.strip_text_after(widget.accessibleName(), ':')) == 'PHASE':
                            self.model.data.runParameterDict[str(self.strip_text_before(widget.accessibleName(), ':'))].update(
                                {'phase': float(str(widget.placeholderText()))})
                    elif self.model.data.runParameterDict[str(self.strip_text_before(widget.accessibleName(), ':'))][
                        'type'] == 'solenoid':
                        self.model.data.runParameterDict[str(widget.accessibleName())].update(
                            {'field_amplitude': float(str(widget.placeholderText()))})
                    elif self.model.data.runParameterDict[str(self.strip_text_before(widget.accessibleName(), ':'))][
                        'type'] == 'generator':
                        self.model.data.runParameterDict[str(widget.accessibleName())].update(
                            {str(widget.accessibleName()): str(widget.placeholderText())})
                else:
                    if self.model.data.runParameterDict[str(self.strip_text_before(widget.accessibleName(), ':'))][
                        'type'] == 'quadrupole':
                        self.model.data.runParameterDict[str(widget.accessibleName())].update({'k1l': float(str(widget.text()))})
                    elif self.model.data.runParameterDict[str(self.strip_text_before(widget.accessibleName(), ':'))][
                        'type'] == 'cavity':
                        if str(self.strip_text_after(widget.accessibleName(), ':')) == 'AMP':
                            self.model.data.runParameterDict[str(self.strip_text_before(widget.accessibleName(), ':'))].update(
                                {'field_amplitude': 1e6*float(str(widget.text()))})
                        elif str(self.strip_text_after(widget.accessibleName(), ':')) == 'PHASE':
                            print('widget.text() = ', widget.text())
                            self.model.data.runParameterDict[str(self.strip_text_before(widget.accessibleName(), ':'))].update(
                                {'phase': float(str(widget.text()))})
                    elif self.model.data.runParameterDict[str(self.strip_text_before(widget.accessibleName(), ':'))][
                        'type'] == 'solenoid':
                        self.model.data.runParameterDict[str(widget.accessibleName())].update(
                            {'field_amplitude': float(str(widget.text()))})
                    elif self.model.data.runParameterDict[str(self.strip_text_before(widget.accessibleName(), ':'))][
                        'type'] == 'generator':
                        self.model.data.runParameterDict[str(widget.accessibleName())].update({'value': str(widget.text())})
            elif str(widget.accessibleName()) in self.model.data.scan_parameter:
                if str(widget.text()) == '':
                    self.model.data.scan_parameter.update({str(widget.accessibleName()): str(widget.placeholderText())})
                else:
                    self.model.data.scan_parameter.update({str(widget.accessibleName()): str(widget.text())})

        if type(widget) is QCheckBox:
            if str(widget.accessibleName()) in self.model.data.runParameterDict:
                if widget.isChecked():
                    self.model.data.runParameterDict[str(widget.accessibleName())].update({'value': True})
                else:
                    self.model.data.runParameterDict[str(widget.accessibleName())].update({'value': False})

    @pyqtSlot()
    def update_value_in_parameter_scan_data(self):
        widget = self.sender()
        if type(widget) is QLineEdit:
            self.model.data.parameterScanDict.update({str(widget.accessibleName()) : str(widget.text())})
        if type(widget) is QCheckBox:
            self.model.data.parameterScanDict.update({str(widget.accessibleName()) : widget.isChecked()})
        if type(widget) is QComboBox:
            runParameter = str(widget.itemText(widget.currentIndex()))
            self.model.data.parameterScanDict.update({str(widget.accessibleName()) : runParameter})
    @pyqtSlot()
    def update_value_in_directory_data(self):
        widget = self.sender()
        if type(widget) is QLineEdit:
            self.model.data.directoryDict.update({str(widget.accessibleName()) : str(widget.text())})

    def initialize_run_parameter_data(self):
        formLayoutList = [formLayout for layout in self.runParameterLayouts for formLayout in layout.findChildren(QFormLayout)]
        #self.model.data.runParameterDict = dict()
        #self.model.data.runParameterDict = self.model.data.runParameterDict
        # print formLayoutList
        # exit()
        for layout in formLayoutList:
            childCount = layout.count()
            for child in range(0,childCount):
                if type(layout.itemAt(child).widget()) is QLineEdit:
                    lineEdit = layout.itemAt(child).widget()
                    lineEdit.textChanged.connect(self.update_value_in_run_parameter_data)
                    #self.model.data.runParameterDict[str(lineEdit.accessibleName())] = str(lineEdit.placeholderText())
                if type(layout.itemAt(child).widget()) is QCheckBox:
                    checkBox = layout.itemAt(child).widget()
                    checkBox.stateChanged.connect(self.update_value_in_run_parameter_data)
                    # if checkBox.isChecked():
                    #     self.model.data.runParameterDict[str(checkBox.accessibleName())] = 'T'
                    # if not checkBox.isChecked():
                    #     self.model.data.runParameterDict[str(checkBox.accessibleName())] = 'F'
        return self.model.data.runParameterDict

    def initialize_parameter_scan_data(self):
        parameterScanDict = dict()
        parameterScanLayout = self.view.parameter_scan_layout
        childCount = parameterScanLayout.count()
        for child in range(0, childCount):
            widget = parameterScanLayout.itemAt(child).widget()
            if type(widget) is QLineEdit:
                parameterScanDict[str(widget.accessibleName())] = str(widget.placeholderText())
                widget.textChanged.connect(self.update_value_in_parameter_scan_data)
            if type(widget) is QComboBox:
                parameterScanDict[str(widget.accessibleName())] = str(widget.currentText())
                widget.currentIndexChanged.connect(self.update_value_in_parameter_scan_data)
            if type(widget) is QCheckBox:
                widget.stateChanged.connect(self.update_value_in_parameter_scan_data)
                if widget.isChecked():
                    parameterScanDict[str(widget.accessibleName())] = True
                if not widget.isChecked():
                    parameterScanDict[str(widget.accessibleName())] = False
        return parameterScanDict

    def initialize_directory_data(self):
        directoryDict = dict()
        directoryLayout = self.view.directory_form_layout
        childCount = directoryLayout.count()
        for child in range(0, childCount):
            widget = directoryLayout.itemAt(child).widget()
            if type(widget) is QLineEdit:
                directoryDict[str(widget.accessibleName())] = str(widget.placeholderText())
                widget.textChanged.connect(self.update_value_in_directory_data)
        return directoryDict

    def get_scannable_parameters_dict(self):
        scannableParameterDict = dict()
        unscannableParameters = ['macro_particle', 'injector_space_charge',
                                 'rest_of_line_space_charge', 'end_of_line']
        for key, value in self.model.data.runParameterDict.items():
            if key not in unscannableParameters:
                if value['type'] == 'cavity':
                    scannableParameterDict[key+'_AMP'] = key
                    scannableParameterDict[key+'_PHASE'] = key
                #parameterDisplayStr = parameter.replace('_', ' ')
                else:
                    scannableParameterDict[key] = key
        return scannableParameterDict

    def populate_scan_combo_box(self):
        scanParameterComboBox = self.view.parameter
        for (parameter, parameterDisplayStr) in self.model.data.scannableParametersDict.items():
            scanParameterComboBox.addItem(parameter)

    def set_line_edit_text_for_run_parameters(self):
        formLayoutList = [formLayout for layout in self.runParameterLayouts for formLayout in layout.findChildren(QFormLayout)]
        for layout in formLayoutList:
            childCount = layout.count()
            for childIndex in range(0, childCount):
                widget = layout.itemAt(childIndex).widget()
                if type(widget) == QLineEdit:
                    value = str(self.model.data.runParameterDict[str(widget.accessibleName())])
                    widget.setText(value)

    def set_check_box_states_for_run_parameters(self):
        formLayoutList = [formLayout for layout in self.runParameterLayouts for formLayout in layout.findChildren(QFormLayout)]
        for layout in formLayoutList:
            childCount = layout.count()
            for childIndex in range(0, childCount):
                widget = layout.itemAt(childIndex).widget()
                if type(widget) == QCheckBox:
                    value = self.model.data.runParameterDict[str(widget.accessibleName())]
                    if value == 'T':
                        widget.setChecked(True)
                    if value == 'F':
                        widiget.setChecked(False)

    def set_line_edit_text_for_scan_parameters(self):
        parameterScanLayout = self.view.parameter_scan_layout
        childCount = parameterScanLayout.count()
        for child in range(0, childCount):
            widget = parameterScanLayout.itemAt(child).widget()
            if type(widget) is QLineEdit:
                widget.setText(str(self.model.data.parameterScanDict[str(widget.accessibleName())]))

    def set_check_box_states_for_scan_parameters(self):
        parameterScanLayout = self.view.parameter_scan_layout
        childCount = parameterScanLayout.count()
        for child in range(0, childCount):
            widget = parameterScanLayout.itemAt(child).widget()
            if type(widget) is QCheckBox:
                widget.setChecked(self.model.data.parameterScanDict[str(widget.accessibleName())])

    def set_combo_box_text_for_scan_parameters(self):
        parameterScanLayout = self.view.parameter_scan_layout
        childCount = parameterScanLayout.count()
        for child in range(0, childCount):
            widget = parameterScanLayout.itemAt(child).widget()
            if type(widget) is QComboBox:
                itemIndex = widget.findText(self.model.data.parameterScanDict[str(widget.accessibleName())])
                widget.setCurrentIndex(itemIndex)

    def set_line_edit_text_for_directory(self):
        directoryLayout = self.view.directory_form_layout
        childCount = directoryLayout.count()
        for child in range(0, childCount):
            widget = directoryLayout.itemAt(child).widget()
            if type(widget) is QLineEdit:
                widget.setText(str(self.model.data.directoryDict[str(widget.accessibleName())]))

    ## Need to port this to the unified controller
    @pyqtSlot()
    def import_parameter_values_from_yaml_file(self):
        dialog = QFileDialog()
        filename = QFileDialog.getOpenFileName(dialog, caption='Open file',
                                                     directory='c:\\',
                                                     filter="YAML files (*.YAML *.YML *.yaml *.yml)")
        if not filename.isEmpty():
            loaded_parameter_dict = yaml_parser.parse_parameter_input_file(filename)
            for (parameter, value) in loaded_parameter_dict.items():
                if parameter in self.model.data.runParameterDict:
                    self.model.data.runParameterDict.update({parameter : value})
                #elif parameter in self.model.data.parameterScanDict:
                #    self.model.data.parameterScanDict.update({parameter : value})
                elif parameter in self.model.data.directoryDict:
                    self.model.data.directoryDict.update({parameter : value})
            self.set_line_edit_text_for_run_parameters()
            self.set_check_box_states_for_run_parameters()
            #self.set_line_edit_text_for_scan_parameters()
            #self.set_check_box_states_for_scan_parameters()
            #self.set_combo_box_text_for_scan_parameters()
            self.set_line_edit_text_for_directory()
        else:
            print('Failed to import, please provide a filename')
    @pyqtSlot()
    def export_parameter_values_to_yaml_file(self):
            export_dict = dict()
            if self.model.data.parameterScanDict['parameter_scan']:
                dialog = QFileDialog()
                directory = QFileDialog.getExistingDirectory(dialog,"Select Directory")
                if not directory == "":
                    scanFrom = float(self.model.data.parameterScanDict['parameter_scan_from_value'])
                    scanTo = float(self.model.data.parameterScanDict['parameter_scan_to_value'])
                    scanStepSize = float(self.model.data.parameterScanDict['parameter_scan_step_size'])
                    currentScanValue = scanFrom
                    parameterToScan = self.model.data.parameterScanDict['parameter']
                    runData = self.model.data.runParameterDict
                    while(currentScanValue <= scanTo):
                        progress = int(100*(currentScanValue/scanTo))
                        print( ' Progression: ', str(progress))
                        self.view.progressBar.setValue(progress)
                        extraParams = None
                        self.get_parameter_to_scan(runData, parameterToScan, currentScanValue)
                        runData[parameterToScan] = currentScanValue
                        filename = os.path.join(str(directory), self.model.data.parameterScanDict['parameter'] + '_' + str(currentScanValue).replace('.','_') + '.YAML')
                        data_dicts = [runData, self.model.data.directoryDict]
                        for dictionary in data_dicts:
                            for key, value in dictionary.items():
                                export_dict.update({key : value})
                        yaml_parser.write_parameter_output_file(filename, export_dict)
                        currentScanValue += scanStepSize
                    self.view.progressBar.setValue(0)
                    self.view.progressBar.format()
                else:
                    print( 'Failed to export, please provide a directory.')
            else:
                dialog = QFileDialog()
                filename, _filter = QFileDialog.getSaveFileNameAndFilter(dialog, caption='Save File', directory='c:\\',
                                                                         filter="YAML Files (*.YAML *.YML *.yaml *.yml")
                if not filename == "":
                    data_dicts = [self.model.data.runParameterDict, self.model.data.directoryDict]
                    for dictionary in data_dicts:
                        for key, value in dictionary.items():
                            if not value == 'sub_elements':
                                export_dict.update({key:value})
                    yaml_parser.write_parameter_output_file(str(filename), export_dict)
                else:
                    print( 'Failed to export, please provide a filename.')

    def get_parameter_to_scan(self, run_dict, parameter_to_scan, current_scan_value):
        if self.strip_text_after(parameter_to_scan, ':') == None:
            if run_dict[self.strip_text_before(parameter_to_scan, ':')]['type'] == "quadrupole":
                run_dict[self.strip_text_before(parameter_to_scan, '')]['k1l'] = current_scan_value
            elif run_dict[self.strip_text_before(parameter_to_scan, ':')]['type'] == "solenoid":
                run_dict[self.strip_text_before(parameter_to_scan, ':')]['field_amplitude'] = current_scan_value
            elif run_dict[self.strip_text_before(parameter_to_scan, ':')]['type'] == "generator":
                run_dict[self.strip_text_before(parameter_to_scan, ':')]['value'] = current_scan_value
        elif self.strip_text_after(parameter_to_scan, ':') == "AMP":
            run_dict[self.strip_text_before(parameter_to_scan, ':')]['field_amplitude'] = current_scan_value
        elif self.strip_text_after(parameter_to_scan, ':') == "PHASE":
            run_dict[self.strip_text_before(parameter_to_scan, ':')]['phase'] = current_scan_value

    def toggle_scan_parameters_state(self):
        performScanCheckbox = self.sender()
        if performScanCheckbox.isChecked():
            self.view.parameter.setEnabled(True)
            self.view.parameter_scan_from_value.setEnabled(True)
            self.view.parameter_scan_to_value.setEnabled(True)
            self.view.parameter_scan_step_size.setEnabled(True)
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

    # def run_thread(self, func):
        # self.thread = GenericThread(func)
        # self.thread.finished.connect(self.enable_run_button)

    # def collect_parameters(self):
        # #layout_list = self.view.centralwidget.findChildren(QGridLayout)
        # for layout_lst in ['centralwidget','layoutWidget','layoutWidget_2']:
            # layout_list = (getattr(self.view, layout_lst)).findChildren(QGridLayout)
            # for layout in layout_list:
                # self.widgets_in_layout(layout)
        # #layout_list = self.view.layoutWidget.findChildren(QGridLayout)
        # #for layout in layout_list:
        # #    self.widgets_in_layout(layout)

    # def widgets_in_layout(self, layout):
        # for children in layout.children():
            # for i in range(0, children.count()):
                # self.widget_names_in_layout(children.itemAt(i).widget())
        # return

    # def widget_names_in_layout(self, widget):
        # if isinstance(widget, QLineEdit):
            # if str(widget.accessibleName()) in self.model.data.self.model.data.runParameterDict.keys():
                # if str(widget.text()) == '':
                    # self.model.data.self.model.data.runParameterDict.update({str(widget.accessibleName()): str(widget.placeholderText())})
                # else:
                    # self.model.data.self.model.data.runParameterDict.update({str(widget.accessibleName()): str(widget.text())})
            # elif str(widget.accessibleName()) in self.model.data.scan_parameter:
                # if str(widget.text()) == '':
                    # self.model.data.scan_parameter.update({str(widget.accessibleName()): str(widget.placeholderText())})
                # else:
                    # self.model.data.scan_parameter.update({str(widget.accessibleName()): str(widget.text())})
        # elif isinstance(widget, QCheckBox):
            # if str(widget.accessibleName()) in self.model.data.self.model.data.runParameterDict:
                # if widget.isChecked():
                    # self.model.data.self.model.data.runParameterDict.update({str(widget.accessibleName()): 'T'})
                # else:
                    # self.model.data.self.model.data.runParameterDict.update({str(widget.accessibleName()): 'F'})
            # elif str(widget.accessibleName()) in self.model.data.scan_parameter:
                # if widget.isChecked():
                   # self.model.data.scan_parameter.update({str(widget.accessibleName()) : True})
                # else:
                   # self.model.data.scan_parameter.update({str(widget.accessibleName()) : False})
        # elif isinstance(widget, QComboBox):
            # self.model.data.scan_parameter.update({str(widget.accessibleName()) : str(widget.currentText())})
        # return

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
        self.disable_run_button()
        self.app_sequence()
        self.enable_run_button()
        #self.run_thread(self.app_sequence)
        #self.thread.start()


    # @pyqtSlot()
    # def handle_existent_file(self):
        # print('Directory '+self.model.data.self.model.data.runParameterDict['directory_line_edit'] + 'already exists')
