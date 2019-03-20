from PyQt4.QtCore import *
from PyQt4.QtGui import *


class Controller(QObject):

    def __init__(self, app, view, model):
        super(Controller, self).__init__()
        self.my_name = 'controller'
        self.app = app
        self.model = model
        self.view = view
        self.model.data.initialise_data()
        self.view.runButton.clicked.connect(self.app_sequence)
        self.disable_run_button()

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
        if self.view.runButton.isChecked():
            self.view.runButton.setEnabled(False)
        else:
            self.view.runButton.setEnabled(True)

    def app_sequence(self):
        self.collect_parameters()
        client = self.model.ssh_to_server()
        self.model.create_subdirectory(client)
        self.model.run_script(client)
        self.model.close_connection(client)
        return
