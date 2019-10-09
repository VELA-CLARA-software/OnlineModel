import PyQt4.QtGui as QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *
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
        self.my_name = 'RunParameterController'
        self.app = app
        self.model = model
        self.view = view
        self.model.data.initialise_data()
        self.model.data.initialise_scan()
        self.model.data.initialise_scan_parameters()
        self.populate_scan_combo_box()
        self.view.runButton.clicked.connect(self.run_astra)

    def populate_scan_combo_box(self):
        parameter_scan_combo_box = self.view.centralwidget.findChild(QComboBox, 'parameter_scan_combo_box')
        for parameter in self.model.data.scan_parameter_list:
            parameter_scan_combo_box.addItem(str(parameter).replace('_line_edit', ''))

    def run_thread(self, func):
        self.thread = GenericThread(func)
        self.thread.finished.connect(self.enable_run_button)

    def collect_parameters(self):
        layout_list = self.view.centralwidget.findChildren(QGridLayout)
        for layout in layout_list:
            self.widgets_in_layout(layout)

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
            elif str(widget.objectName()) in self.model.data.scan_parameters.keys():
                if str(widget.text()) == '':
                    self.model.data.scan_parameters.update({str(widget.objectName()): str(widget.placeholderText())})
                else:
                    self.model.data.scan_parameters.update({str(widget.objectName()): str(widget.text())})
        elif isinstance(widget, QCheckBox):
            if widget.isChecked():
                self.model.data.data_values.update({str(widget.objectName()).replace('_check_box',''): 'T'})
            else:
                self.model.data.data_values.update({str(widget.objectName()).replace('_check_box',''): 'F'})
        elif isinstance(widget, QComboBox):
            self.model.data.scan_parameters.update({str(widget.objectName()) : str(widget.currentText())})
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
    ## Need to port this to the unified controller
    def get_all_line_edits_in_main_window(self):
        line_edit_list = []
        main_window = self.view.centralwidget
        # gather all the children of the central widget
        # which will be the gird layouts containing the line-edits
        # and check-box widgets
        grid_layouts = main_window.findChildren(QLineEdit)
        for widget in grid_layouts:
            if isinstance(widget, QLineEdit):
                line_edit_list.append(widget)
        return line_edit_list
    ## Need to port this to the unified controller
    def get_all_check_boxes_in_main_window(self):
        check_box_list = []
        main_window = self.view.centralwidget
        # gather all the children of the central widget
        # which will be the gird layouts containing the line-edits
        # and check-box widgets
        grid_layouts = main_window.findChildren(QCheckBox)
        for widget in grid_layouts:
            if isinstance(widget, QCheckBox):
                check_box_list.append(widget)
        return check_box_list
    def get_all_combo_boxes_in_main_window(self):
        combo_box_list = []
        main_window = self.view.centralwidget
        grid_layouts = main_window.findChildren(QComboBox)
        for widget in grid_layouts:
            if isinstance(widget, QComboBox):
               combo_box_list.append(widget)
        return combo_box_list
    ## Need to port this to the unified controller
    @staticmethod
    def set_all_line_edits_in_main_window(line_edit_list, values_to_set_dict):
        for line_edit in line_edit_list:
            # our YAML values dict has keys without the '_line_edit' suffix, so we must add this suffix to
            # access the line_edit dict which has keys containing the '_line_edit' suffix.
            line_edit_value_str = str(line_edit.objectName()).replace('_line_edit', '')
            if line_edit_value_str in values_to_set_dict:
                parameter_value_str = str(values_to_set_dict[line_edit_value_str])
                line_edit.setText(parameter_value_str)
                print line_edit_value_str
                print parameter_value_str
    ## Need to port this to the unified controller
    @staticmethod
    def set_all_check_boxes_in_main_window(check_box_list, values_to_set_dict):
        for check_box in check_box_list:
            parameter_value_str = str(values_to_set_dict[str(check_box.objectName()).replace('_check_box', '')])
            # now we convert from T/F to Checked/Unchecked for the check-boxes
            if parameter_value_str == 'T':
                check_box.setChecked(True)
            elif parameter_value_str == 'F':
                check_box.setChecked(False)
    @staticmethod
    def set_combo_box_in_main_window(combo_box_list, values_to_set_dict):
        for combo_box in combo_box_list:
            parameter_value_str = str(values_to_set_dict[str(combo_box.objectName()).replace('_combo_box','')])
            item_index = combo_box.findText(parameter_value_str)
            if (item_index >= 0):
                print combo_box.objectName()
                combo_box.setCurrentIndex(item_index)

    def collect_scan_parameters(self):
        self.model.data.scan_values['parameter_scan'] = self.model.data.scan_parameters['parameter_scan_combo_box']
        self.model.data.scan_values['parameter_scan_from'] = self.model.data.scan_parameters['parameter_scan_from_line_edit']
        self.model.data.scan_values['parameter_scan_to'] = self.model.data.scan_parameters['parameter_scan_to_line_edit']
        self.model.data.scan_values['parameter_scan_step_size'] = self.model.data.scan_parameters['parameter_scan_step_size_line_edit']
    def disable_run_button(self):
        self.view.runButton.setEnabled(False)
        return

    def enable_run_button(self):
        self.view.runButton.setEnabled(True)
        return

    def app_sequence(self):
        self.collect_parameters()
        self.collect_scan_parameters()
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

    @pyqtSlot()
    def handle_existent_file(self):
        print('Directory '+self.model.data.data_values['directory_line_edit'] + 'already exists')

