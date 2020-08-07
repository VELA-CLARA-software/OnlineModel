import sys, os, time, math, datetime, copy, re,  h5py
from collections import OrderedDict
import glob
try:
    from PyQt4.QtCore import *
    from PyQt4.QtGui import *
except:
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *
import pyqtgraph as pg
from pyqtgraph.graphicsItems.LegendItem import ItemSample
import numpy as np
sys.path.append(os.path.abspath(os.path.realpath(__file__)+'/../../../'))
# print (sys.path)
import SimulationFramework.Modules.read_beam_file as raf
import SimulationFramework.Modules.read_twiss_file as rtf
# from SimulationFramework.Modules.online_model_twissPlot import twissPlotWidget
from SimulationFramework.Modules.online_model_slicePlot import slicePlotWidget
from SimulationFramework.Modules.online_model_beamPlot import beamPlotWidget

sys.path.append(os.path.realpath(__file__)+'/../../../../')

class online_model_plotter(QMainWindow):
    def __init__(self, parent = None, directory='.'):
        super(online_model_plotter, self).__init__(parent)
        self.resize(1200,900)

        self.setWindowTitle("ASTRA Data Plotter")
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')

        # reloadSettingsAction = QAction('Reload Settings', self)
        # reloadSettingsAction.setStatusTip('Reload Settings YAML File')
        # reloadSettingsAction.triggered.connect(self.picklePlot.reloadSettings)
        # fileMenu.addAction(reloadSettingsAction)

        exitAction = QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)
        fileMenu.addAction(exitAction)


        self.onlineModelPlotter = onlineModelPlotterWidget(directory=directory)
        self.setCentralWidget(self.onlineModelPlotter)

class onlineModelPlotterWidget(QWidget):
    def __init__(self, parent = None, directory='.'):
        super(onlineModelPlotterWidget, self).__init__()
        self.directory = directory

        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.tabWidget = QTabWidget()

        self.twissPlotWidget = twissPlotWidget()
        self.slicePlotWidget = slicePlotWidget(ymin=0)
        self.beamPlotWidget = beamPlotWidget()

        # self.folderButton = QPushButton('Select Directory')
        # self.folderLineEdit = QLineEdit()
        # # self.folderLineEdit.setReadOnly(True)
        # self.folderLineEdit.setText(self.directory)
        # self.reloadButton = QPushButton()
        # self.reloadButton.setIcon(qApp.style().standardIcon(QStyle.SP_BrowserReload	))
        # self.folderWidget = QGroupBox()
        # self.folderLayout = QHBoxLayout()
        # self.folderLayout.addWidget(self.folderButton)
        # self.folderLayout.addWidget(self.folderLineEdit)
        # self.folderLayout.addWidget(self.reloadButton)
        # self.folderWidget.setLayout(self.folderLayout)
        # self.folderWidget.setMaximumWidth(800)
        # self.reloadButton.clicked.connect(lambda: self.changeDirectory(self.directory))
        # self.folderButton.clicked.connect(self.changeDirectory)

        self.fileSelector = QComboBox()
        self.fileSelector.setMinimumWidth(200)
        self.fileSelector.currentIndexChanged.connect(self.updatePlotButtons)
        self.plotScreenButton = QPushButton('Plot')
        self.plotScreenButton.clicked.connect(self.loadScreen)
        self.removeScreenButton = QPushButton('Remove')
        self.removeScreenButton.clicked.connect(self.removeScreen)
        self.removeScreenButton.setEnabled(False)
        self.beamWidget = QGroupBox()
        self.beamLayout = QHBoxLayout()
        self.beamLayout.addWidget(self.fileSelector)
        # self.beamLayout.addWidget(self.screenSelector)
        self.beamLayout.addWidget(self.plotScreenButton)
        self.beamLayout.addWidget(self.removeScreenButton)
        self.beamWidget.setLayout(self.beamLayout)
        self.beamWidget.setMaximumWidth(800)
        # self.beamWidget.setVisible(True)

        self.sliceWidget = QGroupBox()
        self.sliceWidget.setVisible(False)
        self.sliceLayout = QHBoxLayout()
        self.sliceWidget.setLayout(self.sliceLayout)
        self.sliceLayout.addWidget(self.slicePlotWidget.slicePlotSliceWidthWidget)
        self.sliceWidget.setMaximumWidth(150)

        self.folderBeamWidget = QWidget()
        self.folderBeamLayout = QHBoxLayout()
        self.folderBeamLayout.setAlignment(Qt.AlignLeft);
        self.folderBeamWidget.setLayout(self.folderBeamLayout)
        # self.folderBeamLayout.addWidget(self.folderWidget)
        self.folderBeamLayout.addWidget(self.beamWidget)
        self.folderBeamLayout.addWidget(self.sliceWidget)
        self.plotType = 'Beam'
        # self.tabWidget.addTab(self.twissPlotWidget,'Twiss Plots')
        self.tabWidget.addTab(self.beamPlotWidget,'Beam Plots')
        self.tabWidget.addTab(self.slicePlotWidget,'Slice Beam Plots')

        self.listWidget = QListWidget()
        self.listWidget.setMaximumWidth(200)
        self.listWidget.itemDoubleClicked.connect(self.removeScreen)
        self.listWidget.itemClicked.connect(self.curveClicked)

        self.layout.addWidget(self.folderBeamWidget,0,0,1,2)
        self.layout.addWidget(self.listWidget,1,0,1,1)
        self.layout.addWidget(self.tabWidget,1,1,1,1)

        self.twissDataCounter = 0
        self.changeDirectory(self.directory)
        self.shadowCurves = []
        self.connect_plot_signals()
        self.tabWidget.currentChanged.connect(self.changeTab)

    def connect_plot_signals(self):
        # When either subplot highlights a plot, connect it to the other plot and the listWidget
        self.slicePlotWidget.highlightCurveSignal.connect(lambda x: self.subplotHighlighted(x, 'slicePlotWidget'))
        self.beamPlotWidget.highlightCurveSignal.connect(lambda x: self.subplotHighlighted(x, 'beamPlotWidget'))
        self.slicePlotWidget.unHighlightCurveSignal.connect(lambda x: self.subplotUnHighlighted(x, 'slicePlotWidget'))
        self.beamPlotWidget.unHighlightCurveSignal.connect(lambda x: self.subplotUnHighlighted(x, 'beamPlotWidget'))

    def loadBeamDataFile(self):
        if hasattr(self,'beamFileName') and os.path.isfile(self.directory+'/'+self.beamFileName):
            color = self.beamPlotWidget.addbeamDataFile(self.directory, self.beamFileName)
            self.slicePlotWidget.addsliceDataFile(self.directory+'/'+self.beamFileName, color=color)
            if color is not None:
                self.addBeamToListWidget(self.beamFileName, color)
        self.updatePlotButtons()

    def addBeamToListWidget(self, beamFileName, color):
        widgetItem = QListWidgetItem()
        widgetItem.setFont(QFont('Verdana', weight=QFont.Normal))
        widgetItem.setText(beamFileName)
        pixmap = QPixmap(16, 16)
        if not isinstance(color, QColor):
            color = pg.mkColor(color)
        pixmap.fill(color)
        icon = QIcon(pixmap)
        widgetItem.setIcon(icon)
        self.listWidget.addItem(widgetItem)

    def updatePlotButtons(self):
        if len(self.screenpositions) > 0 and not self.fileSelector.currentText() == '':
            self.beamFileName = str(self.fileSelector.currentData())+'.hdf5'
            if self.directory+'/'+self.beamFileName in self.slicePlotWidget.curves:
                self.plotScreenButton.setText('Update')
                self.removeScreenButton.setEnabled(True)
            else:
                self.plotScreenButton.setText('Plot')
                self.removeScreenButton.setEnabled(False)

    def changeTab(self, i):
        if self.tabWidget.tabText(i) == 'Beam Plots':
            self.plotType = 'Beam'
            self.beamWidget.setVisible(True)
            self.sliceWidget.setVisible(False)
        elif self.tabWidget.tabText(i) == 'Slice Beam Plots':
            self.plotType = 'Slice'
            self.beamWidget.setVisible(True)
            self.sliceWidget.setVisible(True)
        else:
            self.plotType = 'Twiss'
            self.beamWidget.setVisible(False)
            self.sliceWidget.setVisible(False)

    def changeDirectory(self, directory=None, id=None):
        self.directory = directory
        # self.folderLineEdit.setText(self.directory)
        self.currentFileText = self.fileSelector.currentText()
        # self.currentScreenText = self.screenSelector.currentText()
        self.getScreenFiles()
        self.updateFileCombo()
        # self.updateScreenCombo()
        # self.loadTwissDataFile()

    def getSposition(self, file):
        file = h5py.File(self.directory+'/'+file+'.hdf5', "r")
        zpos = file.get('/Parameters/Starting_Position')[2]
        if abs(zpos) < 0.01:
            print(zpos, file)
        return zpos

    def getScreenFiles(self):
        self.screenpositions = {}
        files = glob.glob(self.directory+'/*.hdf5')
        filenames = ['-'.join(os.path.basename(f).split('-')[:2]) for f in files]
        runnumber = ['001' for f in filenames]
        for f in filenames:
            files = glob.glob(self.directory+'/'+f+'*.hdf5')
            screennames = sorted([os.path.basename(s).split('.')[0] for s in files], key=lambda x: self.getSposition(x))
            screenpositions = [self.getSposition(s) for s in screennames]
            self.screenpositions[f] = {'screenpositions': screenpositions, 'screennames': screennames, 'run': '001'}

    def updateFileCombo(self):
        self.fileSelector.clear()
        i = -1
        self.allscreens = []
        for f in self.screenpositions:
            if len(self.screenpositions[f]['screenpositions']) > 0:
                screennames = self.screenpositions[f]['screennames']
                screenpositions = self.screenpositions[f]['screenpositions']
                for n, p in zip(screennames, screenpositions):
                    self.allscreens.append([n, p])
        sortedscreennames = sorted(self.allscreens, key=lambda x: float(x[1]))
        for n,p in sortedscreennames:
            self.fileSelector.addItem(n.ljust(20,' ') + '('+str(p)+'m)',n)
            i += 1
            if f[0] == self.currentFileText:
                self.fileSelector.setCurrentIndex(i)

    def loadScreen(self, i):
        if len(self.screenpositions) > 0 and not self.fileSelector.currentText() == '':
            self.beamFileName = str(self.fileSelector.currentData())+'.hdf5'
            self.loadBeamDataFile()

    def removeScreen(self, item):
        if isinstance(item, QListWidgetItem):
            beamFileName = item.text()
            row = self.listWidget.row(item)
            self.listWidget.takeItem(row)
        else:
            beamFileName = self.beamFileName
        if len(self.screenpositions) > 0 and not self.fileSelector.currentText() == '':
            self.slicePlotWidget.removeCurve(self.directory+'/'+beamFileName)
            self.beamPlotWidget.removePlot(self.directory+'/'+beamFileName)
        self.updatePlotButtons()

    def curveClicked(self, item):
        name = self.directory+'/'+item.text()
        if not name in self.shadowCurves:
            self.highlightPlot(item)
        else:
            self.unHighlightPlot(item)

    def highlightPlot(self, item):
        name = self.directory+'/'+item.text()
        if not name in self.shadowCurves:
            self.shadowCurves.append(name)
            item.setFont(QFont('Verdana', weight=QFont.Bold))
        else:
            self.shadowCurves.remove(name)
            item.setFont(QFont('Verdana', weight=QFont.Normal))
        self.slicePlotWidget.highlightPlot(name)
        self.beamPlotWidget.highlightPlot(name)

    def unHighlightPlot(self, item):
        name = self.directory+'/'+item.text()
        if name in self.shadowCurves:
            self.shadowCurves.remove(name)
            item.setFont(QFont('Verdana', weight=QFont.Normal))
        self.slicePlotWidget.unHighlightPlot(name)
        self.beamPlotWidget.unHighlightPlot(name)

    def subplotHighlighted(self, name, subplot):
        subname = name.split('/')[-1]
        items = self.listWidget.findItems(subname, Qt.MatchExactly)
        if len(items) > 0:
            self.highlightPlot(items[0])

    def subplotUnHighlighted(self, name, subplot):
        subname = name.split('/')[-1]
        items = self.listWidget.findItems(subname, Qt.MatchExactly)
        if len(items) > 0:
            self.unHighlightPlot(items[0])


def main():
    # global app
    import argparse
    parser = argparse.ArgumentParser(description='Analyse Online Model Folder')
    parser.add_argument('-d', '--directory', default='.', type=str)
    args = parser.parse_args()
    pg.setConfigOptions(antialias=True)
    pg.setConfigOption('background', 'w')
    pg.setConfigOption('foreground', 'k')
    app = QApplication(sys.argv)
    ex = online_model_plotter(directory=args.directory)
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
   main()
