import sys
from PyQt5 import QtGui, QtCore, QtWidgets

class scanningTab(QtWidgets.QWidget):
    """Widget that sets scanning parameters."""

    def __init__(self, id, parent=None):
        super(scanningTab, self).__init__(parent)
        self.id = id
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)

        self.scanCheckbox = QtWidgets.QCheckBox()
        self.scanCheckbox.setAccessibleName("scan:parameter"+str(self.id)+"_scan")

        self.scanSelectionLabel = QtWidgets.QLabel('Scan Parameter ' + str(self.id))
        self.scanSelectionWidget = QtWidgets.QComboBox()
        self.scanSelectionWidget.setAccessibleName("scan:parameter"+str(self.id))

        self.scanFromLabel = QtWidgets.QLabel('Scan From')
        self.scanToLabel = QtWidgets.QLabel('Scan To')
        self.scanStepLabel = QtWidgets.QLabel('Scan Step')

        self.scanFromWidget = QtWidgets.QLineEdit()
        self.scanFromWidget.setAccessibleName("scan:parameter"+str(self.id)+"_scan_from_value")
        self.scanToWidget = QtWidgets.QLineEdit()
        self.scanToWidget.setAccessibleName("scan:parameter"+str(self.id)+"_scan_to_value")
        self.scanStepWidget = QtWidgets.QLineEdit()
        self.scanStepWidget.setAccessibleName("scan:parameter"+str(self.id)+"_scan_step_size")

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
    scanTabRemoved = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super(expandableTabWidget, self).__init__(parent)
        self.id = 1
        self.tabs = {}
        # QtGui.QTabWidget.__init__(self, parent)

        # Tab Bar
        self.tab = middleClickTabBar()
        self.setTabBar(self.tab)

        # Properties
        # self.setMovable(True)
        # self.setTabsClosable(True)

        self.plusButton = QtWidgets.QToolButton(self)
        self.plusButton.setText("+")
        self.plusButton.setFixedSize(QtCore.QSize(20, 20))
        self.setCornerWidget(self.plusButton)

        # Signals
        self.plusButton.clicked.connect(self.addScanTab)
        # self.tab.plusClicked.connect(self.addTab)
        # self.tab.tabMoved.connect(self.tab.moveTab)
        self.tab.tabCloseRequested.connect(self.removeScanTab)
        # self.tab.tabCloseRequested.connect(self.removeTab)

    def addScanTab(self):
        tab = scanningTab(self.id)
        self.tabs[self.id] = tab
        self.addTab(tab,'Scan '+str(self.id))
        self.scanTabAdded.emit(self.id)
        self.setCurrentWidget(tab)
        self.id += 1

    def removeScanTab(self, tab):
        id = self.widget(tab).id
        self.scanTabRemoved.emit(id)
        self.removeTab(tab)

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
