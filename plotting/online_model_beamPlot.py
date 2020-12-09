import sys, os, time, math, datetime, copy, re,  h5py
from collections import OrderedDict
import glob
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import pyqtgraph as pg
import numpy as np
sys.path.append(os.path.abspath(os.path.realpath(__file__)+'/../../../SimFrame'))
from SimulationFramework.Modules.Beams import beam as rbfBeam
# sys.path.append(os.path.realpath(__file__)+'/../../../../')

class beamPlotter(QMainWindow):
    """QMainWindow class to demonstrate beamPlot."""

    def __init__(self):
        """Initialise a beamPlotter window."""
        super().__init__()
        self.resize(1800,900)
        self.centralWidget = QWidget()
        self.layout = QVBoxLayout()
        self.centralWidget.setLayout(self.layout)

        self.tab = QTabWidget()
        self.beamPlot = beamPlotWidget()

        self.layout.addWidget(self.beamPlot)

        self.setCentralWidget(self.centralWidget)

        self.setWindowTitle("ASTRA Data Plotter")
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')

        exitAction = QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)
        fileMenu.addAction(exitAction)

class beamPlotWidget(QWidget):
    """Plot object for beam parameters."""

    colors = [QColor('#F5973A'),QColor('#A95AA1'),QColor('#85C059'),QColor('#0F2080'),QColor('#BDB8AD'), 'r', 'k', 'm', 'g']

    beamParams = OrderedDict([
        ['x', {'quantity': 'x', 'units': 'm', 'name': 'x'}],
        ['y', {'quantity': 'y', 'units': 'm', 'name': 'y'}],
        ['z', {'quantity': 'z', 'units': 'm', 'name': 'z', 'norm': True}],
        ['t', {'quantity': 't', 'units': 's', 'name': 't', 'norm': True}],
        ['cpx', {'quantity': 'cpx', 'units': 'eV', 'name': 'cp<sub>x</sub>'}],
        ['cpy', {'quantity': 'cpy', 'units': 'eV', 'name': 'cp<sub>y</sub>'}],
        ['cpz', {'quantity': 'cpz', 'units': 'eV', 'name': 'cp<sub>z</sub>'}],
    ])

    highlightCurveSignal = pyqtSignal(str)
    unHighlightCurveSignal = pyqtSignal(str)

    def __init__(self, **kwargs):
        """Initialise a beam plot object."""
        super().__init__(**kwargs)
        ''' These are for reading data files from ASTRA and Elegant '''
        self.beams = {}

        ''' beamPlotWidget '''
        self.beamPlotWidget = QWidget()
        self.beamPlotLayout = QVBoxLayout()
        self.beamPlotWidget.setLayout(self.beamPlotLayout)

        self.mainBeamPlotLayout = pg.GraphicsLayoutWidget()
        self.mainBeamPlotWidget = self.mainBeamPlotLayout.addPlot(row=0,col=1)
        self.mainBeamPlotWidget.getAxis('bottom').setStyle(showValues=False)
        self.mainBeamPlotWidget.getAxis('left').setStyle(showValues=False)
        self.mainBeamPlotWidget.showAxis('right')
        self.mainBeamPlotWidget.showAxis('top')
        self.mainBeamPlotWidget.getAxis('right').setStyle(showValues=False)
        self.mainBeamPlotWidget.getAxis('top').setStyle(showValues=False)
        self.mainBeamPlotWidget.sigRangeChanged.connect(lambda:self.updateBeamPlot(updatebeam=False, updateprojections=True, updateCurveHighlights=False))
        self.linkAxis = self.mainBeamPlotWidget.vb
        self.bottomBeamPlotLayout = pg.GraphicsLayoutWidget()
        self.bottomBeamPlotWidget = self.mainBeamPlotLayout.addPlot(row=1,col=1)
        self.bottomBeamPlotWidget.setXLink(self.linkAxis)
        self.bottomBeamPlotWidget.setLimits(yMin=0)
        self.bottomBeamPlotWidget.invertY(True)
        self.bottomBeamPlotWidget.getAxis('left').setStyle(showValues=False)
        self.bottomBeamPlotWidget.showAxis('right')
        self.bottomBeamPlotWidget.getAxis('right').setStyle(showValues=False)
        self.rightBeamPlotLayout = pg.GraphicsLayoutWidget()
        self.rightBeamPlotWidget = self.mainBeamPlotLayout.addPlot(row=0,col=0)
        self.rightBeamPlotWidget.setYLink(self.linkAxis)
        self.rightBeamPlotWidget.setLimits(xMin=0)
        self.rightBeamPlotWidget.invertX(True)
        self.rightBeamPlotWidget.getAxis('bottom').setStyle(showValues=False)
        self.rightBeamPlotWidget.showAxis('top')
        self.rightBeamPlotWidget.getAxis('top').setStyle(showValues=False)
        self.mainBeamPlotLayout.ci.layout.setColumnStretchFactor(0, 1)
        self.mainBeamPlotLayout.ci.layout.setColumnStretchFactor(1, 6)
        self.mainBeamPlotLayout.ci.layout.setRowStretchFactor(0, 4)
        self.mainBeamPlotLayout.ci.layout.setRowStretchFactor(1, 1)

        self.pointSize = 3
        self.pointSizeWidget = QSpinBox()
        self.pointSizeWidget.setMaximum(10)
        self.pointSizeWidget.setMinimum(1)
        self.pointSizeWidget.setValue(self.pointSize)
        self.pointSizeWidget.setSingleStep(1)
        self.pointSizeWidget.setSuffix(" px")
        self.pointSizeWidget.setMaximumWidth(150)
        # self.multiaxisPlotAxisLayout.addWidget(self.pointSizeWidget)
        self.pointSizeWidget.valueChanged.connect(self.changePointSize)

        self.beamPlotAxisWidget = QWidget()
        self.beamPlotAxisWidget.setMaximumHeight(100)
        Form = self.beamPlotAxisWidget

        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        self.horizontalLayout = QHBoxLayout(Form)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.beamPlotXAxisCombo = QComboBox(Form)
        self.beamPlotXAxisCombo.addItems(list(self.beamParams.keys()))
        self.beamPlotXAxisCombo.setCurrentIndex(2)
        self.horizontalLayout.addWidget(self.beamPlotXAxisCombo)
        self.beamPlotXAxisNormalise = QCheckBox('Normalise')
        self.beamPlotXAxisNormalise.setChecked(True)
        self.horizontalLayout.addWidget(self.beamPlotXAxisNormalise)
        self.beamPlotYAxisCombo = QComboBox(Form)
        self.beamPlotYAxisCombo.addItems(list(self.beamParams.keys()))
        self.beamPlotYAxisCombo.setCurrentIndex(6)
        self.horizontalLayout.addWidget(self.beamPlotYAxisCombo)
        self.beamPlotYAxisNormalise = QCheckBox('Normalise')
        self.beamPlotYAxisNormalise.setChecked(True)
        self.horizontalLayout.addWidget(self.beamPlotYAxisNormalise)
        self.beamPlotXAxisCombo.currentIndexChanged.connect(lambda:self.updateBeamPlot(updatebeam=True, updateprojections=True, updateCurveHighlights=False))
        self.beamPlotYAxisCombo.currentIndexChanged.connect(lambda:self.updateBeamPlot(updatebeam=True, updateprojections=True, updateCurveHighlights=False))
        self.beamPlotXAxisNormalise.stateChanged.connect(lambda:self.updateBeamPlot(updatebeam=True, updateprojections=True, updateCurveHighlights=False))
        self.beamPlotYAxisNormalise.stateChanged.connect(lambda:self.updateBeamPlot(updatebeam=True, updateprojections=True, updateCurveHighlights=False))

        self.beamPlotLayout.addWidget(self.mainBeamPlotLayout)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.beamPlotAxisWidget)
        self.layout.addWidget(self.beamPlotWidget)

        ''' used for style cycling '''
        self.plotColor = 0
        self.curves = {}
        self.bottomcurves = {}
        self.rightcurves = {}
        self.curve_colors = {}
        self.fillAlpha = {}
        self.shadowCurves = []
        self._histogram_bins = 20

    def addbeamDataFiles(self, dicts):
        """Add beam data files based on a dictionary of directories and filenames."""
        for d in dicts:
            self.addbeamDataFile(**d)

    def addbeamData(self, beamobject, id, color=None):
        ''' addbeamData - takes a "read_beam_file" object and add a plotItem to the relevant self.curves '''
        ''' add the beam object into the self.beams dictionary '''
        ''' Requires a reference file name '''
        if str(type(beamobject)) == "<class 'SimulationFramework.Modules.Beams.beam'>":
            self.beams[id] = beamobject
            if color is None:
                color = self.colors[self.plotColor % len(self.colors)]
                self.plotColor += 1
            pen = pg.mkBrush(color=color)
            self.curve_colors[id] = pg.mkColor(color)
            self.curves[id] = self.mainBeamPlotWidget.plot([], pen=None,
                                                                symbolBrush=pen, symbolSize=self.pointSize, symbolPen=None)
            self.curves[id].sigClicked.connect(lambda: self.curveClicked(id))
            self.add_projected_curves(id)
        self.updateBeamPlot(updatebeam=True, updateprojections=True)
        return color

    def add_projected_curves(self, id):
        """Initialise the marginal plot curves for a new plot."""
        self.bottomcurves[id] = self.bottomBeamPlotWidget.plot([])
        self.bottomcurves[id].rotate(180)
        self.rightcurves[id] = self.rightBeamPlotWidget.plot([])
        self.rightcurves[id].rotate(90)

    def addbeamDataFile(self, directory, filename, color=None, id=None):
        ''' addbeamDataFile - read the data file and add a plotItem to the relevant self.curves '''
        ''' load the data file into the self.beams dictionary '''
        datafile = directory + '/' + filename
        if id is None:
            id = datafile
        if not datafile in self.curves and os.path.isfile(datafile):
            beam = rbfBeam()
            # print('reading beam', datafile)
            beam.read_beam_file(datafile)
            # print('plotting beam', datafile)
            color = self.addbeamData(beam, id=id, color=color)
            return color
        return None

    def get_horizontal_variable(self):
        """Return the x-axis variable name."""
        return self.beamParams[str(self.beamPlotXAxisCombo.currentText())]

    def get_vertical_variable(self):
        """Return the y-axis variable name."""
        return self.beamParams[str(self.beamPlotYAxisCombo.currentText())]

    def updateBeamPlot(self, updatebeam=True, updateprojections=True, updateCurveHighlights=True):
        """Update the main plot and, optionally, marginal plots and curve highlights."""
        xdict = self.beamParams[str(self.beamPlotXAxisCombo.currentText())]
        ydict = self.beamParams[str(self.beamPlotYAxisCombo.currentText())]
        # if updateprojections:
        #     self.rightBeamPlotWidget.clear()
        #     self.bottomBeamPlotWidget.clear()
        for id in self.curves:
            x = getattr(self.beams[id], str(self.beamPlotXAxisCombo.currentText()))
            if self.beamPlotXAxisNormalise.isChecked():
                x = x - np.mean(x)
            y = getattr(self.beams[id], str(self.beamPlotYAxisCombo.currentText()))
            if self.beamPlotYAxisNormalise.isChecked():
                y = y - np.mean(y)
            if updatebeam:
                self.curves[id].setData(x=x, y=y, symbolSize=self.pointSize)

            if updateprojections and id in self.rightcurves and id in self.bottomcurves:
                # self.add_projected_curves(id)
                color = self.curve_colors[id]
                if id in self.fillAlpha:
                    color.setAlpha(self.fillAlpha[id])
                else:
                    color.setAlpha(100)
                xrange, yrange = self.mainBeamPlotWidget.vb.viewRange()
                if len(x) > 0 and len(y) > 0:
                    xy = zip(x,y)
                    xynew = [a for a in xy if a[0] >= xrange[0] and a[0] <= xrange[1] and a[1] >= yrange[0] and a[1] <= yrange[1]]
                    # ynew = [yy for yy in y if yy >= yrange[0] and yy <= yrange[1]]
                    if len(xynew) > 0:
                        xnew, ynew = zip(*xynew)
                        histy, histx = self.projection(ynew, xmult=-1, ymult=1, range=yrange)
                        self.rightcurves[id].setData(x=histx, y=histy, stepMode=True, fillLevel=0, brush=color)
                        # self.rightcurves[id].setData(x=histx, y=histy, stepMode=True, pen=color)
                        histy, histx = self.projection(xnew, xmult=-1, ymult=-1, range=xrange)
                        self.bottomcurves[id].setData(x=histx, y=histy, stepMode=True, fillLevel=0, brush=color)
                        # self.bottomcurves[id].setData(x=histx, y=histy, stepMode=True, pen=color)
        self.rightBeamPlotWidget.setLabel('left', text=ydict['name'], units=ydict['units'], **{'font-size': '12pt', 'font-family': 'Arial'})
        self.bottomBeamPlotWidget.setLabel('bottom', text=xdict['name'], units=xdict['units'], **{'font-size': '12pt', 'font-family': 'Arial'})
        self.rightBeamPlotWidget.enableAutoRange(x=True)
        self.bottomBeamPlotWidget.enableAutoRange(y=True)
        if updateCurveHighlights:
            self.updateCurveHighlights()

    def projection(self, data, xmult=1, ymult=1, range=None):
        """Create projection histogram data."""
        # range[0] = range[0] if range[0] > min(data) else min(data)
        # range[1] = range[1] if range[1] < max(data) else max(data)
        # range[1] = range[1] if range [1] > range[0] else range[0] + 1e-6
        x,y = np.histogram(data, bins=self._histogram_bins, range=None)
        x = np.array([0] + list(x) + [0]) / len(data)
        y = np.array([2*y[0] - y[1]] + list(y) + [2*y[-1] - y[-2]])
        return xmult*x, ymult*y

    def set_histogram_bins(self, bins):
        """Change the number of bins used for generating histogram data."""
        self._histogram_bins = bins
        self.updateBeamPlot(updatebeam=False, updateprojections=True, updateCurveHighlights=False)

    def removePlot(self, id):
        ''' finds all beam plots based on a directory name, and removes them '''
        if id in self.shadowCurves:
            self.shadowCurves.remove(id)
        if id in self.curves:
            self.mainBeamPlotWidget.removeItem(self.curves[id])
            del self.curves[id]
        if id in self.bottomcurves:
            self.bottomBeamPlotWidget.removeItem(self.bottomcurves[id])
            del self.bottomcurves[id]
        if id in self.rightcurves:
            self.rightBeamPlotWidget.removeItem(self.rightcurves[id])
            del self.rightcurves[id]
        self.updateCurveHighlights()
        self.removeData(id)

    def removeData(self, id):
        """Remove a specific beam data object."""
        del self.beams[id]

    def changePointSize(self, size):
        """Change the point size of the main plot."""
        self.pointSize = int(size)
        for d in self.curves.values():
            d.scatter.setSize(int(size))

    def curveClicked(self, name):
        """If a curve is clicked emit the relevant signal."""
        if name in self.shadowCurves:
            self.unHighlightPlot(name)
            self.unHighlightCurveSignal.emit(name)
        else:
            self.highlightPlot(name)
            self.highlightCurveSignal.emit(name)

    def highlightPlot(self, name):
        ''' highlights a particular plot '''
        # print('highligher clicked! = ', name)
        if not isinstance(name, (list, tuple)):
            name = [name]
        for n in name:
            self.addShadowPen(n)
        self.updateCurveHighlights()

    def unHighlightPlot(self, name):
        ''' highlights a particular plot '''
        # print('highligher clicked! = ', name)
        if not isinstance(name, (list, tuple)):
            name = [name]
        for n in name:
            self.removeShadowPen(n)
        self.updateCurveHighlights()

    def updateCurveHighlights(self):
        """If the main plot is changed, update the plot highlights."""
        for n in self.curves.keys():
            if n in self.shadowCurves or not len(self.shadowCurves) > 0:
                self.setPenAlpha(self.curves, n, 255, 3)
                self.setFillAlpha(self.bottomcurves, n, 100)
                self.setFillAlpha(self.rightcurves, n, 100)
            else:
                self.setPenAlpha(self.curves, n, 10, 3)
                self.setFillAlpha(self.bottomcurves, n, 30)
                self.setFillAlpha(self.rightcurves, n, 30)
        self.updateBeamPlot(updatebeam=False, updateprojections=True, updateCurveHighlights=False)

    def addShadowPen(self, name):
        """Add a curve the list of highlighted plots."""
        if not name in self.shadowCurves:
            self.shadowCurves.append(name)

    def removeShadowPen(self, name):
        """Remove a curve from the list of highlighted plots."""
        if name in self.shadowCurves:
            self.shadowCurves.remove(name)

    def setPenAlpha(self, curves, name, alpha=255, width=3):
        """Set the pen alpha value of a specific curve."""
        curve = curves[name]
        pen = curve.opts['symbolBrush']
        pencolor = pen.color()
        pencolor.setAlpha(alpha)
        # pen = pg.mkBrush(color=pencolor, width=width, style=pen.style())
        curve.setSymbolBrush(color=pencolor, width=width, style=pen.style())

    def setFillAlpha(self, curves, name, alpha=255):
        """Set the fill alpha value of a specific curve."""
        self.fillAlpha[name] = alpha

    def clear(self):
        """Remove all plots and reset variables."""
        self.mainBeamPlotWidget.clear()
        self.bottomBeamPlotWidget.clear()
        self.rightBeamPlotWidget.clear()
        self.plotColor = 0
        self.curves = {}
        self.bottomcurves = {}
        self.rightcurves = {}
        self.shadowCurves = []
        self.beams = {}

def main():
    """Main application."""
    app = QApplication(sys.argv)
    # pg.setConfigOptions(antialias=True)
    pg.setConfigOption('background', 'w')
    pg.setConfigOption('foreground', 'k')
    ex = beamPlotter()
    ex.show()
    ex.beamPlot.addbeamDataFiles([
    {'directory': 'OnlineModel_test_data/basefiles_4_250pC', 'filename': 'CLA-S02-APER-01.hdf5'},
    {'directory': 'OnlineModel_test_data/test_4', 'filename': 'CLA-S07-APER-01.hdf5'}])
    sys.exit(app.exec_())

if __name__ == '__main__':
   main()
