import os
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget

class userWidget(QWidget):
    """QWidget that stores the current username."""

    update = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(userWidget, self).__init__()

    def value(self):
        """Return the username."""
        return os.getlogin()
