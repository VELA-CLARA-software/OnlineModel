import time
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget

class timeWidget(QWidget):
    """QWidget that stores the current time."""
    update = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(timeWidget, self).__init__()

    def value(self):
        """Return the time."""
        return time.time()
