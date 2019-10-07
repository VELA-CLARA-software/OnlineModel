from PyQt4.QtCore import *
from PyQt4.QtGui import *


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
		super(Controller, self).__init__()
		self.my_name = 'controller'
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
			elif str(widget.objectName()) in self.model.data.scan_parameter:
				if str(widget.text()) == '':
					self.model.data.scan_parameter.update({str(widget.objectName()): str(widget.placeholderText())})
				else:
					self.model.data.scan_parameter.update({str(widget.objectName()): str(widget.text())})
		elif isinstance(widget, QCheckBox):
			if widget.isChecked():
				self.model.data.data_values.update({str(widget.objectName()): 'T'})
			else:
				self.model.data.data_values.update({str(widget.objectName()): 'F'})
		elif isinstance(widget, QComboBox):
			self.model.data.scan_parameter.update({str(widget.objectName()) : str(widget.currentText())})
		return
	def collect_scan_parameters(self):
		self.model.data.scan_values['parameter'] = self.model.data.scan_parameter['parameter_scan_combo_box']
		self.model.data.scan_values['from'] = self.model.data.scan_parameter['parameter_scan_from_value_line_edit']
		self.model.data.scan_values['to'] = self.model.data.scan_parameter['parameter_scan_to_value_line_edit']
		self.model.data.scan_values['step'] = self.model.data.scan_parameter['parameter_scan_step_size_line_edit']
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

