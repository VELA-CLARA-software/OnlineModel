import PyQt4.QtGui as QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from copy import copy,deepcopy


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
        self.model.data.initialise_scan()
        self.model.data.initialise_scan_parameters()
        self.populate_scan_combo_box()
        self.view.parameter_scan_check_box.stateChanged.connect(self.toggle_scan_parameters_state)
        self.view.parameter_scan_check_box.setChecked(True)

    def toggle_scan_parameters_state(self, state):
        # parameter_scan_combo_box = self.view.centralwidget.findChild(QComboBox, 'parameter_scan_combo_box')
        # parameter_scan_from_value_line_edit = self.view.centralwidget.findChild(QLineEdit,
        #                                                                         'parameter_scan_from_value_line_edit')
        # parameter_scan_to_value_line_edit = self.view.centralwidget.findChild(QLineEdit,
        #                                                                       'parameter_scan_to_value_line_edit')
        # parameter_scan_step_size_line_edit = self.view.centralwidget.findChild(QLineEdit,
        #                                                                        'parameter_scan_step_size_line_edit')
        parameter_scan_combo_box = self.view.layoutWidget.findChild(QComboBox, 'parameter_scan_combo_box')
        parameter_scan_from_value_line_edit = self.view.layoutWidget.findChild(QLineEdit, 'parameter_scan_from_value_line_edit')
        parameter_scan_to_value_line_edit = self.view.layoutWidget.findChild(QLineEdit, 'parameter_scan_to_value_line_edit')
        parameter_scan_step_size_line_edit = self.view.layoutWidget.findChild(QLineEdit, 'parameter_scan_step_size_line_edit')
        if (state > 0):
            parameter_scan_combo_box.setEnabled(True)
            parameter_scan_from_value_line_edit.setEnabled(True)
            parameter_scan_to_value_line_edit.setEnabled(True)
            parameter_scan_step_size_line_edit.setEnabled(True)
        else:
            parameter_scan_combo_box.setEnabled(False)
            parameter_scan_from_value_line_edit.setEnabled(False)
            parameter_scan_to_value_line_edit.setEnabled(False)
            parameter_scan_step_size_line_edit.setEnabled(False)

    def populate_scan_combo_box(self):
        # parameter_scan_combo_box = self.view.centralwidget.findChild(QComboBox, 'parameter_scan_combo_box')
        parameter_scan_combo_box = self.view.layoutWidget.findChild(QComboBox, 'parameter_scan_combo_box')
        for parameter in self.model.data.scan_parameter_list:
            parameter_scan_combo_box.addItem(str(parameter).replace('_line_edit', ''))

    def run_thread(self, func):
        self.thread = GenericThread(func)
        self.thread.finished.connect(self.enable_run_button)

    def collect_parameters(self):
        #layout_list = self.view.centralwidget.findChildren(QGridLayout)
        for layout_lst in ['centralwidget','layoutWidget','layoutWidget_2']:
            layout_list = (getattr(self.view, layout_lst)).findChildren(QGridLayout)
            for layout in layout_list:
                self.widgets_in_layout(layout)
        #layout_list = self.view.layoutWidget.findChildren(QGridLayout)
        #for layout in layout_list:
        #    self.widgets_in_layout(layout)

    def widgets_in_layout(self, layout):
        for children in layout.children():
            for i in range(0, children.count()):
                self.widget_names_in_layout(children.itemAt(i).widget())
        return

    def widget_names_in_layout(self, widget):
        if isinstance(widget, QLineEdit):
            if str(widget.objectName()) in self.model.data.data_values.keys():
                if str(widget.text()) == '':
                    self.model.data.data_values.update({str(widget.objectName()): str(widget.placeholderText())})
                else:
                    self.model.data.data_values.update({str(widget.objectName()): str(widget.text())})
            elif str(widget.objectName()) in self.model.data.scan_parameter:
                if str(widget.text()) == '':
                    self.model.data.scan_parameter.update({str(widget.objectName()): str(widget.placeholderText())})
                else:
                    self.model.data.scan_parameter.update({str(widget.objectName()): str(widget.text())})
        elif isinstance(widget, QCheckBox):
            if str(widget.objectName()) in self.model.data.data_values:
                if widget.isChecked():
                    self.model.data.data_values.update({str(widget.objectName()): 'T'})
                else:
                    self.model.data.data_values.update({str(widget.objectName()): 'F'})
            elif str(widget.objectName()) in self.model.data.scan_parameter:
                if widget.isChecked():
                   self.model.data.scan_parameter.update({str(widget.objectName()) : True})
                else:
                   self.model.data.scan_parameter.update({str(widget.objectName()) : False})
        elif isinstance(widget, QComboBox):
            self.model.data.scan_parameter.update({str(widget.objectName()) : str(widget.currentText())})
        return

    ## Need to port this to the unified controller
    def import_parameter_values_from_yaml_file(self):
        dialog = QtGui.QFileDialog()
        filename = QtGui.QFileDialog.getOpenFileName(dialog, caption='Open file',
                                                     directory='c:\\',
                                                     filter="YAML files (*.YAML *.YML *.yaml *.yml)")  
        if not filename.isEmpty():
            loaded_parameter_list = yaml_parser.parse_parameter_input_file(filename)
            line_edit_list = self.get_all_line_edits_in_main_window()
            self.set_all_line_edits_in_main_window(line_edit_list,loaded_parameter_list)
            check_box_list = self.get_all_check_boxes_in_main_window()
            self.set_all_check_boxes_in_main_window(check_box_list, loaded_parameter_list)
            combo_box_list = self.get_all_combo_boxes_in_main_window()
            self.set_combo_box_in_main_window(combo_box_list, loaded_parameter_list)
        else:
            print 'Failed to import, please provide a filename'

    def export_parameter_values_to_yaml_file(self):
        dialog = QtGui.QFileDialog()
        dialog.setFileMode(QtGui.QFileDialog.DirectoryOnly)
        filename, _filter = QtGui.QFileDialog.getSaveFileNameAndFilter(dialog, caption='Save File', directory='c:\\',
                                                                    filter="YAML Files (*.YAML *.YML *.yaml *.yml")
        # we have a validation check in collect_line_edit_text() called by collect_parameters()
        # so if a value isn't valid, that entry for the data.parameters is not set.
        #
        # Currently, this means that if we have an invalid input, the yaml file isn't written out.
        # However, all of this is implicit. So need to find a way to explicitly validate for YAML exporting
        if not filename.isEmpty():
            self.collect_parameters()
            self.collect_scan_parameters()
            export_dict = dict(self.model.data.data_values)
            export_dict.update(self.model.data.scan_values)
            # IF validate(parameter_values) THEN:
            yaml_parser.write_parameter_output_file(filename, export_dict)
            # ELSE: RAISE EXCEPTION/DISPLAY INVALID INPUT TO USER
        else:
            print 'Failed to export, please provide a filename.'

    def collect_scan_parameters(self):
        self.model.data.scan_values['parameter_scan'] = self.model.data.scan_parameter['parameter_scan_combo_box']
        self.model.data.scan_values['parameter_scan_from'] = self.model.data.scan_parameter['parameter_scan_from_line_edit']
        self.model.data.scan_values['parameter_scan_to'] = self.model.data.scan_parameter['parameter_scan_to_line_edit']
        self.model.data.scan_values['parameter_scan_step_size'] = self.model.data.scan_parameter['parameter_scan_step_size_line_edit']

    def disable_run_button(self):
        self.view.runButton.setEnabled(False)
        return

    def enable_run_button(self):
        self.view.runButton.setEnabled(True)
        return

    def app_sequence(self):
        self.collect_parameters()
        self.collect_scan_parameters()
        self.model.ssh_to_server()
        self.model.create_subdirectory()
        if self.model.path_exists:
            self.thread.stop()
            self.thread.finished.connect(self.enable_run_button())
            self.thread.signal.connect(self.handle_existent_file)

        else:
            self.thread._stopped = False
        self.model.run_script()
        return

    def run_astra(self):
        self.disable_run_button()
        #self.app_sequence()
        #self.enable_run_button()
        self.run_thread(self.app_sequence)
        self.thread.start()

    @pyqtSlot()
    def handle_existent_file(self):
        print('Directory '+self.model.data.data_values['directory_line_edit'] + 'already exists')

