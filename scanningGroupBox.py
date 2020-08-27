import sys
from PyQt5 import QtGui, QtCore, QtWidgets

class ButtonGroupBox(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(ButtonGroupBox, self).__init__(parent=parent)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0,24,0,0)
        self.groupBox = QtWidgets.QGroupBox(self)
        self.button = QtWidgets.QPushButton("Disable Scanning", parent=self)
        self.layout.addWidget(self.groupBox)

        self.button.move(0, -4)

    def __getattr__(self, attr):
        if hasattr(self, attr):
            return super(ButtonGroupBox, self).__getattr__(self, attr)
        else:
            return getattr(self.groupBox, attr)
