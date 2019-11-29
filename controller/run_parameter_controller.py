from PyQt4.QtCore import *
from PyQt4.QtGui import *
from copy import copy,deepcopy
import run_parameters_parser as yaml_parser
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
        self.model.data.runParameterDict = self.initialize_run_parameter_data()
        self.model.data.scannableParametersDict = self.get_scannable_parameters_dict()
        self.populate_scan_combo_box()
        self.model.data.parameterScanDict = self.initialize_parameter_scan_data()
        self.model.data.directoryDict = self.initialize_directory_data()
        #self.model.data.initialise_scan()
        #self.model.data.initialise_scan_parameters()

        #self.view.parameter_scan_check_box.stateChanged.connect(self.toggle_scan_parameters_state)
        #self.view.parameter_scan_check_box.setChecked(True)
    @pyqtSlot()
    def update_value_in_run_parameter_data(self):
        widget = self.sender()
        if type(widget) is QLineEdit:
            self.model.data.runParameterDict.update({str(widget.objectName()) : str(widget.text())})
        if type(widget) is QCheckBox:
            if widget.isChecked():
                self.model.data.runParameterDict.update({str(widget.objectName()) : 'T'})
            if not widget.isChecked():
                self.model.data.runParameterDict.update({str(widget.objectName()) : 'F'})
    @pyqtSlot()
    def update_value_in_parameter_scan_data(self):
        widget = self.sender()
        if type(widget) is QLineEdit:
            self.model.data.parameterScanDict.update({str(widget.objectName()) : str(widget.text())})
        if type(widget) is QCheckBox:
            self.model.data.parameterScanDict.update({str(widget.objectName()) : widget.isChecked()})
        if type(widget) is QComboBox:
            runParameter = str(widget.itemText(widget.currentIndex()))
            self.model.data.parameterScanDict.update({str(widget.objectName()) : runParameter})
    @pyqtSlot()
    def update_value_in_directory_data(self):
        widget = self.sender()
        if type(widget) is QLineEdit:
            self.model.data.directoryDict.update({str(widget.objectName()) : str(widget.text())})

    def initialize_run_parameter_data(self):
        runParameterLayouts = [self.view.non_magnet_arguments_layout,
                               self.view.magnet_quad_strength_layout]
        formLayoutList = [formLayout for layout in runParameterLayouts for formLayout in layout.findChildren(QFormLayout)]
        runParameterDict = dict()
        for layout in formLayoutList:
            childCount = layout.count()
            for child in range(0,childCount):
                if type(layout.itemAt(child).widget()) is QLineEdit:
                    lineEdit = layout.itemAt(child).widget()
                    lineEdit.textChanged.connect(self.update_value_in_run_parameter_data)
                    runParameterDict[str(lineEdit.objectName())] = str(lineEdit.placeholderText())
                if type(layout.itemAt(child).widget()) is QCheckBox:
                    checkBox = layout.itemAt(child).widget()
                    checkBox.stateChanged.connect(self.update_value_in_run_parameter_data)
                    if checkBox.isChecked():
                        runParameterDict[str(checkBox.objectName())] = 'T'
                    if not checkBox.isChecked():
                        runParameterDict[str(checkBox.objectName())] = 'F'
        return runParameterDict
        
    def initialize_parameter_scan_data(self):
        parameterScanDict = dict()
        parameterScanLayout = self.view.parameter_scan_layout
        childCount = parameterScanLayout.count()
        for child in range(0, childCount):
            widget = parameterScanLayout.itemAt(child).widget()
            if type(widget) is QLineEdit:
                parameterScanDict[str(widget.objectName())] = str(widget.placeholderText())
                widget.textChanged.connect(self.update_value_in_parameter_scan_data)
            if type(widget) is QComboBox:
                parameterScanDict[str(widget.objectName())] = str(widget.currentText())
                widget.currentIndexChanged.connect(self.update_value_in_parameter_scan_data)
            if type(widget) is QCheckBox:
                widget.stateChanged.connect(self.update_value_in_parameter_scan_data)
                if widget.isChecked():
                    parameterScanDict[str(widget.objectName())] = True
                if not widget.isChecked():
                    parameterScanDict[str(widget.objectName())] = False
        return parameterScanDict

    def initialize_directory_data(self):
        directoryDict = dict()
        directoryLayout = self.view.directory_form_layout
        childCount = directoryLayout.count()
        for child in range(0, childCount):
            widget = directoryLayout.itemAt(child).widget()
            if type(widget) is QLineEdit:
                directoryDict[str(widget.objectName())] = str(widget.placeholderText())
                widget.textChanged.connect(self.update_value_in_directory_data)
        return directoryDict

    def get_scannable_parameters_dict(self):
        scannableParameterDict = dict()
        unscannableParameters = ['macro_particle', 'injector_space_charge', 
                                 'rest_of_line_space_charge', 'end_of_line']
        for parameter in self.model.data.runParameterDict:
            if parameter not in unscannableParameters:
                parameterDisplayStr = parameter.replace('_', ' ')
                scannableParameterDict[parameter] = parameter
        return scannableParameterDict

    def populate_scan_combo_box(self):
        scanParameterComboBox = self.view.parameter
        for (parameter, parameterDisplayStr) in self.model.data.scannableParametersDict.items():
            scanParameterComboBox.addItem(parameterDisplayStr)
    
    def set_line_edit_text_for_run_parameters(self):
        runParameterLayouts = [self.view.non_magnet_arguments_layout,
                               self.view.magnet_quad_strength_layout]
        formLayoutList = [formLayout for layout in runParameterLayouts for formLayout in layout.findChildren(QFormLayout)]
        for layout in formLayoutList:
            childCount = layout.count()
            for childIndex in range(0, childCount):
                widget = layout.itemAt(childIndex).widget()
                if type(widget) == QLineEdit:
                    value = self.model.data.runParameterDict[str(widget.objectName())]
                    widget.setText(value)

    def set_check_box_states_for_run_parameters(self):
        runParameterLayouts = [self.view.non_magnet_arguments_layout,
                               self.view.magnet_quad_strength_layout]
        formLayoutList = [formLayout for layout in runParameterLayouts for formLayout in layout.findChildren(QFormLayout)]
        for layout in formLayoutList:
            childCount = layout.count()
            for childIndex in range(0, childCount):
                widget = layout.itemAt(childIndex).widget()
                if type(widget) == QCheckBox:
                    value = self.model.data.runParameterDict[str(widget.objectName())]
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
                print str(widget.objectName())
                widget.setText(self.model.data.parameterScanDict[str(widget.objectName())])

    def set_check_box_states_for_scan_parameters(self):
        parameterScanLayout = self.view.parameter_scan_layout
        childCount = parameterScanLayout.count()
        for child in range(0, childCount):
            widget = parameterScanLayout.itemAt(child).widget()
            if type(widget) is QCheckBox:
                print str(widget.objectName())
                widget.setChecked(self.model.data.parameterScanDict[str(widget.objectName())])

    def set_combo_box_text_for_scan_parameters(self):
        parameterScanLayout = self.view.parameter_scan_layout
        childCount = parameterScanLayout.count()
        for child in range(0, childCount):
            widget = parameterScanLayout.itemAt(child).widget()
            if type(widget) is QComboBox:
                print str(widget.objectName())
                itemIndex = widget.findText(self.model.data.parameterScanDict[str(widget.objectName())])
                widget.setCurrentIndex(itemIndex)
                
    def set_line_edit_text_for_directory(self):
        directoryLayout = self.view.directory_form_layout
        childCount = directoryLayout.count()
        for child in range(0, childCount):
            widget = directoryLayout.itemAt(child).widget()
            if type(widget) is QLineEdit:
                widget.setText(self.model.data.directoryDict[str(widget.objectName())])

    ## Need to port this to the unified controller
    @pyqtSlot()
    def import_parameter_values_from_yaml_file(self):
        print 'IMPORT CALLED'
        dialog = QFileDialog()
        filename = QFileDialog.getOpenFileName(dialog, caption='Open file',
                                                     directory='c:\\',
                                                     filter="YAML files (*.YAML *.YML *.yaml *.yml)")  
        if not filename.isEmpty():
            loaded_parameter_dict = yaml_parser.parse_parameter_input_file(filename)
            for (parameter, value) in loaded_parameter_dict.items():
                if parameter in self.model.data.runParameterDict:
                    self.model.data.runParameterDict.update({parameter : value})
                elif parameter in self.model.data.parameterScanDict:
                    self.model.data.parameterScanDict.update({parameter : value})
                elif parameter in self.model.data.directoryDict:
                    self.model.data.directoryDict.update({parameter : value})
                # NEED TO SET LINE EDITS TO RUN PARAMETER DICT VALUES
            self.set_line_edit_text_for_run_parameters()
            self.set_check_box_states_for_run_parameters()
            self.set_line_edit_text_for_scan_parameters()
            self.set_check_box_states_for_scan_parameters()
            self.set_combo_box_text_for_scan_parameters()
            self.set_line_edit_text_for_directory()
        else:
            print 'Failed to import, please provide a filename'
    @pyqtSlot()
    def export_parameter_values_to_yaml_file(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.DirectoryOnly)
        filename, _filter = QFileDialog.getSaveFileNameAndFilter(dialog, caption='Save File', directory='c:\\',
                                                                    filter="YAML Files (*.YAML *.YML *.yaml *.yml")
        if not filename.isEmpty():
            export_dict = dict()
            data_dicts = [self.model.data.runParameterDict,
                          self.model.data.parameterScanDict,
                          self.model.data.directoryDict]
            for dictionary in data_dicts:
                for key, value in dictionary.items():
                    export_dict.update({key : value})
            yaml_parser.write_parameter_output_file(filename, export_dict)
            # ELSE: RAISE EXCEPTION/DISPLAY INVALID INPUT TO USER
        else:
            print 'Failed to export, please provide a filename.'
            
    # def toggle_scan_parameters_state(self, state):
        # # parameter_scan_combo_box = self.view.centralwidget.findChild(QComboBox, 'parameter_scan_combo_box')
        # # parameter_scan_from_value_line_edit = self.view.centralwidget.findChild(QLineEdit,
        # #                                                                         'parameter_scan_from_value_line_edit')
        # # parameter_scan_to_value_line_edit = self.view.centralwidget.findChild(QLineEdit,
        # #                                                                       'parameter_scan_to_value_line_edit')
        # # parameter_scan_step_size_line_edit = self.view.centralwidget.findChild(QLineEdit,
        # #                                                                        'parameter_scan_step_size_line_edit')
        # parameter_scan_combo_box = self.view.layoutWidget.findChild(QComboBox, 'parameter_scan_combo_box')
        # parameter_scan_from_value_line_edit = self.view.layoutWidget.findChild(QLineEdit, 'parameter_scan_from_value_line_edit')
        # parameter_scan_to_value_line_edit = self.view.layoutWidget.findChild(QLineEdit, 'parameter_scan_to_value_line_edit')
        # parameter_scan_step_size_line_edit = self.view.layoutWidget.findChild(QLineEdit, 'parameter_scan_step_size_line_edit')
        # if (state > 0):
            # parameter_scan_combo_box.setEnabled(True)
            # parameter_scan_from_value_line_edit.setEnabled(True)
            # parameter_scan_to_value_line_edit.setEnabled(True)
            # parameter_scan_step_size_line_edit.setEnabled(True)
        # else:
            # parameter_scan_combo_box.setEnabled(False)
            # parameter_scan_from_value_line_edit.setEnabled(False)
            # parameter_scan_to_value_line_edit.setEnabled(False)
            # parameter_scan_step_size_line_edit.setEnabled(False)



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
            # if str(widget.objectName()) in self.model.data.data_values.keys():
                # if str(widget.text()) == '':
                    # self.model.data.data_values.update({str(widget.objectName()): str(widget.placeholderText())})
                # else:
                    # self.model.data.data_values.update({str(widget.objectName()): str(widget.text())})
            # elif str(widget.objectName()) in self.model.data.scan_parameter:
                # if str(widget.text()) == '':
                    # self.model.data.scan_parameter.update({str(widget.objectName()): str(widget.placeholderText())})
                # else:
                    # self.model.data.scan_parameter.update({str(widget.objectName()): str(widget.text())})
        # elif isinstance(widget, QCheckBox):
            # if str(widget.objectName()) in self.model.data.data_values:
                # if widget.isChecked():
                    # self.model.data.data_values.update({str(widget.objectName()): 'T'})
                # else:
                    # self.model.data.data_values.update({str(widget.objectName()): 'F'})
            # elif str(widget.objectName()) in self.model.data.scan_parameter:
                # if widget.isChecked():
                   # self.model.data.scan_parameter.update({str(widget.objectName()) : True})
                # else:
                   # self.model.data.scan_parameter.update({str(widget.objectName()) : False})
        # elif isinstance(widget, QComboBox):
            # self.model.data.scan_parameter.update({str(widget.objectName()) : str(widget.currentText())})
        # return

    # def collect_scan_parameters(self):
        # self.model.data.scan_values['parameter_scan'] = self.model.data.scan_parameter['parameter_scan_combo_box']
        # self.model.data.scan_values['parameter_scan_from_value'] = self.model.data.scan_parameter['parameter_scan_from_value_line_edit']
        # self.model.data.scan_values['parameter_scan_to_value'] = self.model.data.scan_parameter['parameter_scan_to_value_line_edit']
        # self.model.data.scan_values['parameter_scan_step_size'] = self.model.data.scan_parameter['parameter_scan_step_size_line_edit']

    # def disable_run_button(self):
        # self.view.runButton.setEnabled(False)
        # return

    # def enable_run_button(self):
        # self.view.runButton.setEnabled(True)
        # return

    # def app_sequence(self):
        # self.collect_parameters()
        # self.collect_scan_parameters()
        # self.model.ssh_to_server()
        # self.model.create_subdirectory()
        # if self.model.path_exists:
            # self.thread.stop()
            # self.thread.finished.connect(self.enable_run_button())
            # self.thread.signal.connect(self.handle_existent_file)

        # else:
            # self.thread._stopped = False
        # self.model.run_script()
        # return

    # def run_astra(self):
        # self.disable_run_button()
        # #self.app_sequence()
        # #self.enable_run_button()
        # self.run_thread(self.app_sequence)
        # self.thread.start()

    # @pyqtSlot()
    # def handle_existent_file(self):
        # print('Directory '+self.model.data.data_values['directory_line_edit'] + 'already exists')



    # def get_all_line_edits_in_main_window(self):
        # line_edit_list = []
        # main_window = self.view.layoutWidget
        # # gather all the children of the central widget
        # # which will be the gird layouts containing the line-edits
        # # and check-box widgets
        # grid_layouts = main_window.children()
        # for widget in grid_layouts:
            # if isinstance(widget, QLineEdit):
                # line_edit_list.append(widget)
        # return line_edit_list

    # def get_all_check_boxes_in_main_window(self):
        # check_box_list = []
        # main_window = self.view.layoutWidget
        # # gather all the children of the central widget
        # # which will be the gird layouts containing the line-edits
        # # and check-box widgets
        # grid_layouts = main_window.children()
        # for widget in grid_layouts:
            # if isinstance(widget, QCheckBox):
                # check_box_list.append(widget)
        # return check_box_list   

    # def set_all_line_edits_in_main_window(self, line_edit_list, values_to_set_dict):
        # print values_to_set_dict
        # for line_edit in line_edit_list:
            # # our YAML values dict has keys without the '_line_edit' suffix, so we must add this suffix to
            # # access the line_edit dict which has keys containing the '_line_edit' suffix.
            # print str(line_edit.objectName()).replace("_line_edit", "")
            # parameter_value_str = str(values_to_set_dict[str(line_edit.objectName()).replace("_line_edit", "")])
            # line_edit.setText(parameter_value_str)

    # def set_combo_box_in_main_window(self, combo_box_list, values_to_set_dict):
        # for combo_box in combo_box_list:
            # print str(line_edit.objectName()).replace("_combo_box", "")
            # combo_box_value_str = str(values_to_set_dict[str(combo_box.objectName()).replace("_combo_box", "")])
            # if combo_box_value_str == 'T':
              # combo_box.setChecked(True)
            # if combo_box_value_str == 'F':
              # combo_box.setChecked(False)



