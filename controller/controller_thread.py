from PyQt4.QtCore import *
from PyQt4.QtGui import *


class GenericThread(QThread):
    def __init__(self, function, *args, **kwargs):
        QThread.__init__(self)
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def __del__(self):
        self.wait()

    def run(self):
        self.object = self.function(*self.args, **self.kwargs)


class Controller(QObject):

    def __init__(self, app, view, model):
        super(Controller, self).__init__()
        self.my_name = 'controller'
        self.app = app
        self.model = model
        self.view = view
        self.model.data.initialise_data()
        self.view.runButton.clicked.connect(self.run_astra)

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

    def disable_run_button(self):
        self.view.runButton.setEnabled(False)
        return

    def enable_run_button(self):
        self.view.runButton.setEnabled(True)
        return

    def app_sequence(self):
        self.collect_parameters()
        self.model.ssh_to_server()
        self.model.create_subdirectory()
        self.model.run_script()
        return

    def run_astra(self):
        self.disable_run_button()
        self.run_thread(self.app_sequence)
        self.thread.start()
