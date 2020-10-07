import sys
from PyQt5 import QtGui, QtCore, QtWidgets
from collections import OrderedDict

class scanningTab(QtWidgets.QWidget):
    """Widget that sets scanning parameters."""

    def __init__(self, id, parent=None):
        super(scanningTab, self).__init__(parent)
        self.id = id
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)

        self.scanCheckbox = QtWidgets.QCheckBox()

        self.scanSelectionLabel = QtWidgets.QLabel()
        self.scanSelectionWidget = QtWidgets.QComboBox()

        self.scanFromLabel = QtWidgets.QLabel('Scan From')
        self.scanToLabel = QtWidgets.QLabel('Scan To')
        self.scanStepLabel = QtWidgets.QLabel('Scan Step')

        self.scanFromWidget = QtWidgets.QLineEdit()
        self.scanToWidget = QtWidgets.QLineEdit()
        self.scanStepWidget = QtWidgets.QLineEdit()

        self.scanSelectionWidget.setEnabled(False)
        self.scanFromWidget.setEnabled(False)
        self.scanToWidget.setEnabled(False)
        self.scanStepWidget.setEnabled(False)

        self.layout.addWidget(self.scanCheckbox,0,0,1,1)
        self.layout.addWidget(self.scanSelectionLabel,0,1,1,1)
        self.layout.addWidget(self.scanSelectionWidget,0,2,1,5)
        self.layout.addWidget(self.scanFromLabel,1,0,1,2)
        self.layout.addWidget(self.scanFromWidget,1,2,1,1)
        self.layout.addWidget(self.scanToLabel,1,3,1,1)
        self.layout.addWidget(self.scanToWidget,1,4,1,1)
        self.layout.addWidget(self.scanStepLabel,1,5,1,1)
        self.layout.addWidget(self.scanStepWidget,1,6,1,1)

        self.scanCheckbox.stateChanged.connect(self.toggle_scan_parameters_state)

    def set_id(self, id):
        self.id = id
        self.scanCheckbox.setAccessibleName("scan:"+str(id)+":scan")
        self.scanSelectionLabel.setText('Scan Parameter ' + str(id))
        self.scanSelectionWidget.setAccessibleName("scan:"+str(id)+':parameter')
        self.scanFromWidget.setAccessibleName("scan:"+str(id)+":scan_from_value")
        self.scanToWidget.setAccessibleName("scan:"+str(id)+":scan_to_value")
        self.scanStepWidget.setAccessibleName("scan:"+str(id)+":scan_step_size")

    def toggle_scan_parameters_state(self):
        if self.scanCheckbox.isChecked():
            self.scanSelectionWidget.setEnabled(True)
            self.scanFromWidget.setEnabled(True)
            self.scanToWidget.setEnabled(True)
            self.scanStepWidget.setEnabled(True)
            # self.update_widget_from_dict('scan:parameter')
            # self.update_widget_from_dict('scan:parameter_scan_from_value')
            # self.update_widget_from_dict('scan:parameter_scan_to_value')
            # self.update_widget_from_dict('scan:parameter_scan_step_size')
        else:
            self.scanSelectionWidget.setEnabled(False)
            self.scanFromWidget.setEnabled(False)
            self.scanToWidget.setEnabled(False)
            self.scanStepWidget.setEnabled(False)

class middleClickTabBar(QtWidgets.QTabBar):

    def __init__(self, parent=None):
        super(middleClickTabBar, self).__init__(parent)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.MidButton:
            self.tabCloseRequested.emit(self.tabAt(event.pos()))
        super(QtWidgets.QTabBar, self).mouseReleaseEvent(event)


class expandableTabWidget(QtWidgets.QTabWidget):
    """Tab Widget that that can have new tabs easily added to it."""

    scanTabAdded = QtCore.pyqtSignal(int)
    scanTabRemoved = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        super(expandableTabWidget, self).__init__(parent)
        self.id = 1
        self.tabs = OrderedDict()
        # QtGui.QTabWidget.__init__(self, parent)

        # Tab Bar
        self.tab = middleClickTabBar()
        self.setTabBar(self.tab)

        # Properties
        # self.setMovable(True)
        # self.setTabsClosable(True)
        self.buttonWidget = QtWidgets.QWidget()
        self.buttonWidgetLayout = QtWidgets.QHBoxLayout()
        self.buttonWidgetLayout.setSpacing(0)
        self.buttonWidgetLayout.setContentsMargins(0,0,0,0)
        self.buttonWidget.setLayout(self.buttonWidgetLayout)
        # Add tab button
        self.plusButton = QtWidgets.QToolButton(self)
        self.plusButton.setText("+")
        self.plusButton.setFixedSize(QtCore.QSize(20, 20))
        self.plusButton.setToolTip('Add Scanning Dimension')
        self.buttonWidgetLayout.addWidget(self.plusButton)
        # Clear scanning checkboxes
        self.clearButton = QtWidgets.QToolButton(self)
        self.clearButton.setText("Clear")
        self.clearButton.setFixedSize(QtCore.QSize(35, 20))
        self.clearButton.setToolTip('Clear all Scan checkboxes')
        self.buttonWidgetLayout.addWidget(self.clearButton)
        # Set Corner widget
        self.setCornerWidget(self.buttonWidget)

        # Signals
        self.plusButton.clicked.connect(self.addScanTab)
        self.clearButton.clicked.connect(self.clearScans)
        self.tab.tabCloseRequested.connect(self.removeScanTab)

    def addScanTab(self):
        tab = scanningTab(0)
        self.addTab(tab,'')
        self.setCurrentWidget(tab)
        self.relabel_tabs()
        self.scanTabAdded.emit(tab.id)

    def removeScanTab(self, index):
        id = self.widget(index).id
        tab = self.widget(index)
        self.removeTab(index)
        tab.deleteLater()
        self.relabel_tabs()
        self.scanTabRemoved.emit(tab.layout)
        if not self.tab.count() > 0:
            self.addScanTab()

    def relabel_tabs(self):
        tabs = {}
        for i in range(self.tab.count()):
            v = self.widget(i)
            v.set_id(i+1)
            tabs[i+1] = v
            self.setTabText(i, 'Scan '+str(i+1))
        self.tabs = tabs

    def clearScans(self):
        for id, tab in self.tabs.items():
            tab.scanCheckbox.setCheckState(QtCore.Qt.Unchecked)

class TabExample(QtWidgets.QMainWindow):
    def __init__(self):
        super(TabExample, self).__init__()
        self.setWindowTitle("Tab example")

        # Create widgets
        self.tab_widget = expandableTabWidget()
        self.setCentralWidget(self.tab_widget)

        # Label's to fill widget
        self.label1 = QtWidgets.QLabel("Tab 1")
        self.label2 = QtWidgets.QLabel("Tab 2")

        # Adding tab's
        self.tab_widget.addTab(self.label1, "Tab 1")
        self.tab_widget.addTab(self.label2, "Tab 2")

        self.show()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    gui = TabExample()
    sys.exit(app.exec_())
