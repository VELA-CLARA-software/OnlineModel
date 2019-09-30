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
            self.model.data.data_values.update({str(widget.objectName()): str(widget.text())})
        elif isinstance(widget, QCheckBox):
            if widget.isChecked():
                self.model.data.data_values.update({str(widget.objectName()): 'T'})
            else:
                self.model.data.data_values.update({str(widget.objectName()): 'F'})
        return
	
	def import_parameter_values_from_yaml_file(self):
	    dialog = Qt.FileDialog()
	    filename = Qt.QFileDialog.getOpenFileName(dialog, caption='Open file',
                                                  directory='c:\\',
											      filter="YAML files (*.YAML *.YML *.yaml *.yml)")	
	    if not filename.isEmpty():
		    loaded_parameter_list = yaml_parser.parse_parameter_input_file(filename)
			line_edit_list = self.get_all_line_edits_in_main_window()
			self.set_all_line_edits_in_main_window(line_edit_list,loaded_parameter_list)
			# get all check boxes
			# set all check box
			
			
	def get_all_line_edits_in_main_window(self):
		line_edit_list = []
		main_window = self.ui.centralwidget
		# gather all the children of the central widget
		# which will be the gird layouts containing the line-edits
		# and check-box widgets
		grid_layouts = main_window.children()
		for widget in grid_layouts:
			if isinstance(widget, Qt.QLineEdit):
				line_edit_list.append(widget)
		return line_edit_list

    def get_all_check_boxes_in_main_window(self):
        check_box_list = []
        main_window = self.ui.centralwidget
        # gather all the children of the central widget
        # which will be the gird layouts containing the line-edits
        # and check-box widgets
        grid_layouts = main_window.children()
        for widget in grid_layouts:
            if isinstance(widget, Qt.QCheckBox):
                check_box_list.append(widget)
        return check_box_list	
        @staticmethod
    def set_all_line_edits_in_main_window(line_edit_list, values_to_set_dict):
        print values_to_set_dict
        for line_edit in line_edit_list:
            # our YAML values dict has keys without the '_line_edit' suffix, so we must add this suffix to
            # access the line_edit dict which has keys containing the '_line_edit' suffix.
            parameter_value_str = str(values_to_set_dict[str(line_edit.objectName()).replace('_line_edit', '')])
            line_edit.setText(parameter_value_str)

    def disable_run_button(self):
        self.view.runButton.setEnabled(False)
        return

    def enable_run_button(self):
        print 'called run_button_enabled'
        self.view.runButton.setEnabled(True)
        return

    def app_sequence(self):
        self.collect_parameters()
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

    @pyqtSlot()
    def handle_existent_file(self):
        print('Directory '+self.model.data.data_values['directory_line_edit'] + 'already exists')

