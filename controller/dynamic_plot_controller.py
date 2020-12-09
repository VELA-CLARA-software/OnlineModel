from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sys, os
import database.run_parameters_parser as yaml_parser
from plotting.online_model_twissPlot import twissPlotWidget
from plotting.online_model_plotter_run_id import onlineModelPlotterWidget

class DynamicPlotController(QObject):
    """Controlller object for managing dynamic plots."""

    plotcolor = pyqtSignal(int, QColor)

    def __init__(self, app, view, model):
        """Initialise a DynamicPlotController object, passing in the app, view and model objects."""
        super(DynamicPlotController, self).__init__()
        self.my_name = 'controller'
        self.app = app
        self.model = model
        self.view = view
        self.ompbeam = onlineModelPlotterWidget(self.model.data.screenDict, directory='.')
        self.view.plots_yaml_tab.insertTab(0, self.ompbeam, "Plots")
        self.view.plots_yaml_tab.setCurrentIndex(0)
        self.clickedCurve = None

    def set_base_directory(self, directory):
        """Set the base directory location."""
        self.basedirectoryname = directory

    def curveClicked(self, name):
        """When a curve is clicked on the plot, send a signal to the relevant plotting objects."""
        self.ompbeam.curveClicked(name)

    def add_plot(self, id, dir):
        """Add a plot to the plot object passing the run ID and the run directory, and emit a plotcolor signal."""
        color = self.ompbeam.addRunIDToListWidget(self.basedirectoryname+'/'+dir, self.model.dbcontroller.find_run_id_for_each_lattice(dir))
        self.plotcolor.emit(id, color)

    def remove_plot(self, dir):
        """Remove a plot from the plotting object."""
        self.ompbeam.removeRunIDFromListWidget(self.basedirectoryname+'/'+dir)
