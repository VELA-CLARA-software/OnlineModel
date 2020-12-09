from PyQt5.QtCore import pyqtSignal, QThread, QObject, QRunnable, pyqtSlot
from PyQt5.QtWidgets import QWidget
#from PyQt5.QtGui import *

class GenericThread(QThread):
    """Generic QThread object."""
    signal = pyqtSignal()

    def __init__(self, function, *args, **kwargs):
        super(GenericThread, self).__init__()
        self._stopped = False
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def __del__(self):
        self.wait()

    def stop(self):
        """Stop the thread."""
        self._stopped = True

    def run(self):
        """Start the thread."""
        self.signal.emit()
        if not self._stopped:
            self.object = self.function(*self.args, **self.kwargs)

class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        `tuple` (exctype, value, traceback.format_exc() )

    result
        `object` data returned from processing, anything

    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)

class OMWorkerThread(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(OMWorkerThread, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            pass
        self.signals.finished.emit()  # Done

class signalling_monitor(QObject):
    """QObject that emits a signal when a variable changes value."""
    valueChanged = pyqtSignal(int)

    def __init__(self, ref, parameter, interval=200):
        super(signalling_monitor, self).__init__()
        self.timer = QTimer(self)
        self.timer.setInterval(interval)
        self.timer.timeout.connect(self.emitValue)
        self.ref = ref
        self.parameter = parameter

    def stop(self):
        """Stop the timer."""
        self.timer.stop()

    def start(self, interval=None):
        """Start the timer."""
        self.setInterval(interval)
        self.timer.start()

    def setInterval(self, interval):
        """Change the timer interval."""
        if interval is not None:
            self.timer.setInterval(interval)

    def emitValue(self):
        """Emit a valueChanged signal with the new value."""
        self.valueChanged.emit(getattr(self.ref, self.parameter))
