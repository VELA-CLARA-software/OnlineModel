import sys, os
from collections import OrderedDict
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import pyqtgraph as pg
sys.path.append(os.path.abspath(os.path.realpath(__file__)+'/../'))
from plotting.online_model_twissPlot import globalTwissPlotWidget, latticeTwissPlotWidget, beamTwissPlotWidget
from plotting.online_model_slicePlot import slicePlotWidget
from plotting.online_model_beamPlot import beamPlotWidget

class online_model_plotter(QMainWindow):
    def __init__(self, screenpositions, parent = None, directory='.'):
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


        self.onlineModelPlotter = onlineModelPlotterWidget(screenpositions, directory=directory)
        self.setCentralWidget(self.onlineModelPlotter)

class HTMLDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        self.initStyleOption(option,index)
        painter.save()
        doc = QTextDocument()
        doc.setHtml(option.text)
        option.text = ""
        option.widget.style().drawControl(QStyle.CE_ItemViewItem, option, painter)

        painter.translate(option.rect.left(), option.rect.top())
        clip = QtCore.QRectF(0, 0, option.rect.width(), option.rect.height())
        doc.drawContents(painter, clip)
        painter.restore()

    def sizeHint(self, option, index):
        self.initStyleOption(option,index)
        doc = QTextDocument()
        doc.setHtml(option.text)
        doc.setTextWidth(option.rect.width())
        return QSize(doc.idealWidth(), doc.size().height())

class onlineModelPlotterWidget(QWidget):

    colors = [QColor('#F5973A'),QColor('#A95AA1'),QColor('#85C059'),QColor('#0F2080'),QColor('#BDB8AD'), 'r', 'k', 'm', 'g']
    twissFunctions = [
                ['run_id', '', 1],
                ['beta_x', '&beta;<sub>x</sub> [m]', 1],
                ['alpha_x', '&alpha;<sub>x</sub>', 1],
                ['beta_y', '&beta;<sub>y</sub> [m]', 1],
                ['alpha_y', '&alpha;<sub>y</sub>', 1],
                ['beta_x_beam', '&beta;<sub>x,beam</sub> [m]', 1],
                ['alpha_x_beam', '&alpha;<sub>x,beam</sub>', 1],
                ['beta_y_beam', '&beta;<sub>y,beam</sub> [m]', 1],
                ['alpha_y_beam', '&alpha;<sub>y,beam</sub>', 1],
                ['sigma_x', '&sigma;<sub>x</sub> [mm]', 1e3],
                ['sigma_y', '&sigma;<sub>y</sub> [mm]', 1e3],
                ['eta_x', '&eta;<sub>x</sub> [mm]', 1e3],
                ['eta_xp', '&eta;<sub>x</sub>\' [mm]', 1e3],
                ['eta_x_beam', '&eta;<sub>x,beam</sub> [mm]', 1e3],
                ['eta_xp_beam', '&eta;<sub>x,beam</sub>\' [mm]', 1e3],
                ['cp_eV', 'cp [MeV/c]', 1e-6],
                ['sigma_cp_eV', '&sigma;<sub>cp</sub> [keV/c]', 1e-3],
                ['sigma_z', '&sigma;<sub>z</sub> [mm]', 1e3],
                ['sigma_t', '&sigma;<sub>t</sub> [fs]', 1e15],
                ['enx', '&epsilon;<sub>x,n</sub> [mm-mrad]', 1e6],
                ['eny', '&epsilon;<sub>y,n</sub> [mm-mrad]', 1e6],
                ['ecnx', '&epsilon;<sub>x,n,c</sub> [mm-mrad]', 1e6],
                ['ecny', '&epsilon;<sub>y,n,c</sub> [mm-mrad]', 1e6],
                ]

    def __init__(self, screenpositions, parent = None, directory='.'):
        super(onlineModelPlotterWidget, self).__init__()
        self.screenpositions = screenpositions
        self.directory = directory
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.tabWidget = QTabWidget()

        self.globalTwissPlotWidget = globalTwissPlotWidget()
        self.latticeTwissPlotWidget = latticeTwissPlotWidget()
        self.beamTwissPlotWidget = beamTwissPlotWidget()
        self.slicePlotWidget = slicePlotWidget(ymin=0)
        self.beamPlotWidget = beamPlotWidget()
        self.twissTableWidget = QTableWidget()
        self.twissTableWidget.setColumnCount(2)

        self.plotColor = 0
        self.run_id_prefixes = {}
        self.run_id_color = {}

        self.fileSelector = QComboBox()
        self.fileSelector.setMinimumWidth(200)
        self.fileSelector.currentIndexChanged.connect(self.loadScreen)
        self.fileSelector.currentIndexChanged.connect(self.loadTwissTable)
        self.beamWidget = QGroupBox()
        self.beamLayout = QHBoxLayout()
        self.beamLayout.addWidget(self.fileSelector)
        self.beamWidget.setLayout(self.beamLayout)
        self.beamWidget.setMaximumWidth(800)

        self.sliceWidget = QGroupBox()
        self.sliceWidget.setVisible(False)
        self.sliceLayout = QHBoxLayout()
        self.sliceWidget.setLayout(self.sliceLayout)
        self.sliceLayout.addWidget(self.slicePlotWidget.slicePlotSliceWidthWidget)
        self.slicePlotWidget.slicePlotSliceWidthWidget.valueChanged.connect(self.beamPlotWidget.set_histogram_bins)
        self.sliceWidget.setMaximumWidth(150)

        self.pointSizeWidget = QGroupBox()
        self.pointSizeWidget.setVisible(False)
        self.pointSizeLayout = QHBoxLayout()
        self.pointSizeWidget.setLayout(self.pointSizeLayout)
        self.pointSizeLayout.addWidget(self.beamPlotWidget.pointSizeWidget)
        self.pointSizeWidget.setMaximumWidth(150)

        self.folderBeamWidget = QWidget()
        self.folderBeamLayout = QHBoxLayout()
        self.folderBeamLayout.setAlignment(Qt.AlignLeft);
        self.folderBeamWidget.setLayout(self.folderBeamLayout)
        self.folderBeamLayout.addWidget(self.beamWidget)
        self.folderBeamLayout.addWidget(self.sliceWidget)
        self.folderBeamLayout.addWidget(self.pointSizeWidget)

        self.plotType = 'Twiss'
        self.tabWidget.addTab(self.globalTwissPlotWidget,'Beam Sigmas')
        self.tabWidget.addTab(self.latticeTwissPlotWidget,'Lattice Twiss')
        self.tabWidget.addTab(self.beamTwissPlotWidget,'Beam Twiss')
        self.tabWidget.addTab(self.beamPlotWidget,'Scatter Plots')
        self.tabWidget.addTab(self.slicePlotWidget,'Slice Properties')
        self.tabWidget.addTab(self.twissTableWidget,'Twiss Table')


        self.layout.addWidget(self.folderBeamWidget,0,0,1,2)
        self.layout.addWidget(self.tabWidget,1,1,1,1)

        self.twissDataCounter = 0
        self.changeDirectory(self.directory)
        self.shadowCurves = []
        self.connect_plot_signals()
        self.tabWidget.currentChanged.connect(self.changeTab)
        self.fileSelector.currentIndexChanged.connect(self.loadScreen)
        self.fileSelector.currentIndexChanged.connect(self.loadTwissTable)

    def connect_plot_signals(self):
        # When either subplot highlights a plot, connect it to the other plot and the listWidget
        self.globalTwissPlotWidget.highlightCurveSignal.connect(self.subplotHighlighted)
        self.latticeTwissPlotWidget.highlightCurveSignal.connect(self.subplotHighlighted)
        self.beamTwissPlotWidget.highlightCurveSignal.connect(self.subplotHighlighted)
        self.slicePlotWidget.highlightCurveSignal.connect(self.subplotHighlighted)
        self.beamPlotWidget.highlightCurveSignal.connect(self.subplotHighlighted)
        self.globalTwissPlotWidget.unHighlightCurveSignal.connect(self.subplotUnHighlighted)
        self.latticeTwissPlotWidget.unHighlightCurveSignal.connect(self.subplotUnHighlighted)
        self.beamTwissPlotWidget.unHighlightCurveSignal.connect(self.subplotUnHighlighted)
        self.slicePlotWidget.unHighlightCurveSignal.connect(self.subplotUnHighlighted)
        self.beamPlotWidget.unHighlightCurveSignal.connect(self.subplotUnHighlighted)

    def loadBeamDataFile(self, directory, beamFileName, color, id):
        if os.path.isfile(directory+'/'+beamFileName):
            self.beamPlotWidget.addbeamDataFile(directory, beamFileName, id=id, color=color)
            self.slicePlotWidget.addsliceDataObject(self.beamPlotWidget.beams[id], id=id, color=color)

    def addRunIDToListWidget(self, run_id, prefixes, color=None):
        self.run_id_prefixes[run_id] = prefixes
        if color is None:
            color = self.colors[self.plotColor % len(self.colors)]
            self.plotColor += 1
        self.run_id_color[run_id] = color
        if not isinstance(color, QColor):
            color = pg.mkColor(color)
        self.run_id_color[run_id] = color
        self.loadTwiss(run_id)
        self.loadScreen()
        self.loadTwissTable()
        return color

    def removeRunIDFromListWidget(self, run_id):
        del self.run_id_prefixes[run_id]
        self.globalTwissPlotWidget.removeCurve(run_id)
        self.latticeTwissPlotWidget.removeCurve(run_id)
        self.beamTwissPlotWidget.removeCurve(run_id)
        self.slicePlotWidget.removeCurve(run_id)
        self.beamPlotWidget.removePlot(run_id)
        self.loadTwissTable()

    def changeTab(self, i):
        if self.tabWidget.tabText(i) == 'Scatter Plots':
            self.plotType = 'Beam'
            self.pointSizeWidget.setVisible(True)
            self.sliceWidget.setVisible(True)
        elif self.tabWidget.tabText(i) == 'Slice Properties':
            self.plotType = 'Slice'
            self.pointSizeWidget.setVisible(False)
            self.sliceWidget.setVisible(True)
        else:
            self.plotType = 'Twiss'
            self.pointSizeWidget.setVisible(False)
            self.sliceWidget.setVisible(False)

    def changeDirectory(self, directory=None, id=None):
        self.currentFileText = self.fileSelector.currentText()
        self.updateFileCombo()

    def updateFileCombo(self):
        self.fileSelector.clear()
        i = -1
        self.allscreens = []
        for l, f in self.screenpositions.items():
            for k, v in f.items():
                n = k
                p = v['position']
                self.allscreens.append([n, p, l])
        sortedscreennames = sorted(self.allscreens, key=lambda x: float(x[1]))
        selected = False
        for n,p,l in sortedscreennames:
            self.fileSelector.addItem(n.ljust(20,' ') + '('+str(p)+'m)',[n,p])
            i += 1
            if n == self.currentFileText:
                self.fileSelector.setCurrentIndex(i)
                selected = True
        if not selected:
            self.fileSelector.setCurrentIndex(3)

    def loadTwiss(self, id):
        prefixes = self.run_id_prefixes[id]
        twissList = []
        for s, d in prefixes.items():
            twissList.append({'directory': 'test/'+d, 'sections': [s]})
        twiss, id, color = self.globalTwissPlotWidget.addTwissDirectory(twissList, id=id, color=self.run_id_color[id])
        self.latticeTwissPlotWidget.addtwissDataObject(twiss, id, color=color)
        self.beamTwissPlotWidget.addtwissDataObject(twiss, id, color=color)

    def label_widget(self, text=''):
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setEnabled(False)
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(label)
        widget.setLayout(layout)
        return widget

    def loadTwissTable(self):
        self.twissTableWidget.clearContents()
        self.twissTableWidget.setColumnCount(len(self.run_id_prefixes) + 1)
        self.twissTableWidget.setRowCount(len(self.twissFunctions))
        zpos = self.fileSelector.currentData()[1]
        for row, twiss in enumerate(self.twissFunctions):
            self.twissTableWidget.setCellWidget(row, 0, self.label_widget(twiss[1]))
        for col, run_id in enumerate(self.run_id_prefixes):
            twissData = self.globalTwissPlotWidget.twissDataObjects[run_id]
            for row, twiss in enumerate(self.twissFunctions):
                if twiss[0] == 'run_id':
                    colorWidget = pg.ColorButton()
                    colorWidget.setEnabled(False)
                    colorWidget.setColor(self.run_id_color[run_id])
                    self.twissTableWidget.setCellWidget(row, 1+col, colorWidget)
                else:
                    self.twissTableWidget.setItem(row, 1+col, QTableWidgetItem(str(round(twiss[2]*twissData.get_parameter_at_z(twiss[0], zpos),2))))

    def loadScreen(self):
        self.clearBeamScreens()
        if len(self.screenpositions) > 0 and not self.fileSelector.currentText() == '':
            beamfilename = str(self.fileSelector.currentData()[0])+'.hdf5'
            screens, positions, lattices = list(zip(*self.allscreens))
            screen_idx = screens.index(self.fileSelector.currentData()[0])
            lattice = lattices[screen_idx]
            for run, prefixes in self.run_id_prefixes.items():
                directory = 'test/' + prefixes[lattice]
                color = self.run_id_color[run]
                self.loadBeamDataFile(directory, beamfilename, color, run)

    def curveClicked(self, item):
        if isinstance(item, str):
            name = item
        else:
            name = item.text()
        if name in self.run_id_prefixes:
            if not name in self.shadowCurves:
                self.highlightPlot(item)
            else:
                self.unHighlightPlot(item)

    def get_run_id_directory(self, run_id):
        beamfilename = str(self.fileSelector.currentData()[0])+'.hdf5'
        screens, positions, lattices = list(zip(*self.allscreens))
        screen_idx = screens.index(self.fileSelector.currentData()[0])
        lattice = lattices[screen_idx]
        prefix = self.run_id_prefixes[run_id]
        directory = 'test/' + prefix[lattice]
        return directory+'/'+run_id

    def highlightPlot(self, name):
        if name in self.run_id_prefixes and not name in self.shadowCurves:
            self.shadowCurves.append(name)
        self.globalTwissPlotWidget.highlightPlot(name)
        self.latticeTwissPlotWidget.highlightPlot(name)
        self.beamTwissPlotWidget.highlightPlot(name)
        self.slicePlotWidget.highlightPlot(name)
        self.beamPlotWidget.highlightPlot(name)

    def unHighlightPlot(self, name):
        if name in self.run_id_prefixes and name in self.shadowCurves:
            self.shadowCurves.remove(name)
        self.globalTwissPlotWidget.unHighlightPlot(name)
        self.latticeTwissPlotWidget.unHighlightPlot(name)
        self.beamTwissPlotWidget.unHighlightPlot(name)
        self.slicePlotWidget.unHighlightPlot(name)
        self.beamPlotWidget.unHighlightPlot(name)

    def subplotHighlighted(self, name):
        subname = name.split('/')[-1]
        self.highlightPlot(subname)

    def subplotUnHighlighted(self, name):
        subname = name.split('/')[-1]
        self.unHighlightPlot(subname)

    def clearBeamScreens(self):
        self.beamPlotWidget.clear()
        self.slicePlotWidget.clear()

def main():
    # global app
    import argparse
    parser = argparse.ArgumentParser(description='Analyse Online Model Folder')
    parser.add_argument('-d', '--directory', default='.', type=str)
    args = parser.parse_args()
    import ruamel.yaml as yaml
    yaml.add_representer(OrderedDict, yaml.representer.SafeRepresenter.represent_dict)
    with open(r'C:\Users\jkj62\Documents\GitHub\ASTRA_COMPARISONRunner-HMCC\screen_positions.yaml', 'r') as stream:
        yaml_parameter_dict = yaml.safe_load(stream)
    # print(yaml_parameter_dict)
    pg.setConfigOptions(antialias=True)
    pg.setConfigOption('background', 'w')
    pg.setConfigOption('foreground', 'k')
    app = QApplication(sys.argv)
    ex = online_model_plotter(yaml_parameter_dict,directory=args.directory)
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
   main()
