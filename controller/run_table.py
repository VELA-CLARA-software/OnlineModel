from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import pyqtgraph as pg

class LoadButtonDelegate(QStyledItemDelegate):
    def __init__(self, owner, rpc):
        super().__init__(owner)
        self.owner = owner
        self.rpc = rpc

    def paint(self, painter, option, index):
        if isinstance(self.parent(), QAbstractItemView):
            self.parent().openPersistentEditor(index)
        super(LoadButtonDelegate, self).paint(painter, option, index)

    def createEditor(self, parent, option, index):
        loadButton = QPushButton('Load', parent)
        loadButton.clicked.connect(lambda: self.rpc.load_yaml_from_db(self.get_id(index)))
        return loadButton

    def get_id(self, index):
        return index.siblingAtColumn(1).data()

class PlotCheckboxDelegate(QItemDelegate):
    """
    A delegate that places a fully functioning QCheckBox cell of the column to which it's applied.
    """
    def __init__(self, parent, rpc):
        QItemDelegate.__init__(self, parent)
        self.owner = parent
        self.rpc = rpc

    def createEditor(self, parent, option, index):
        """
        Important, otherwise an editor is created if the user clicks in this cell.
        """
        return None

    def paint(self, painter, option, index):
        """
        Paint a checkbox without the label.
        """
        painter.drawText(option.rect.translated(-1,0), Qt.AlignRight|Qt.AlignVCenter, "Plot")
        self.drawCheck(painter, option, option.rect.translated(-10,0), Qt.Checked if self.get_id(index) in self.rpc.run_plots else Qt.Unchecked)

    def get_id(self, index):
        return index.siblingAtColumn(1).data()

    def editorEvent(self, event, model, option, index):
        '''
        Change the data in the model and the state of the checkbox
        if the user presses the left mousebutton and this cell is editable. Otherwise do nothing.
        '''
        if event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
            self.rpc.emit_plot_signals(index.row(), self.get_id(index), not self.get_id(index) in self.rpc.run_plots)
            return True
        return False

class PlotColorDelegate(LoadButtonDelegate):

    def createEditor(self, parent, option, index):
        colorWidget = pg.ColorButton(parent)
        colorWidget.setEnabled(False)
        if self.get_id(index) in self.rpc.run_plots:
            colorWidget.setColor(self.rpc.run_plot_colors[self.get_id(index)])
            return colorWidget
        return None

class RunModel(QAbstractTableModel):
    ActiveRole = Qt.UserRole + 1

    def __init__(self, data, timestamps=None, rpc=None, parent=None):
        super().__init__()
        self._data = data
        self._timestamps = timestamps
        self._rpc = rpc
        self.currentSortDirection = None

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return 5

    def sort(self, column=None, direction=0):
        """ 
            - only able to sort if column = 4 (timestamp) for now.
            - Direction=0 -> ASCENDING
            - Direction=1 -> DESCENDING
        """

        self.layoutAboutToBeChanged.emit()
        self.currentSortDirection = direction
        if column == 4:
            self._rpc.emit_sort_by_timestamp_signal(column, direction)
            self._timestamps=dict(sorted(self._timestamps.items(), key=lambda x: x[1],reverse=(not direction)))
            self._data = list(self._timestamps.keys())
            self.modelReset.emit()
        print('SORT CALLED on column: ', column)
        print('SORT ORDER: ', direction)
       

    def data(self, index, role):
        if role == Qt.DisplayRole:
            if index.column() == 1:
                return QVariant(self._data[index.row()])
            elif index.column() == 4:
                return QVariant(self._timestamps[self._data[index.row()]]) 
            else:
                return None
