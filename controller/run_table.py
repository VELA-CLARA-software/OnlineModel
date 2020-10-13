from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import pyqtgraph as pg
from copy import copy

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
        # return self.owner.model()._data[index.row()]
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
        return self.owner.model()._data[index.row()]
        # return index.siblingAtColumn(1).data()

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
        # print(index.row(), index.siblingAtColumn(1).data(), index.siblingAtColumn(1).data() in self.rpc.run_plots)
        if index.siblingAtColumn(1).data() in self.rpc.run_plots:
            colorWidget = pg.ColorButton(parent)
            colorWidget.setEnabled(False)
            colorWidget.setColor(self.rpc.run_plot_colors[index.siblingAtColumn(1).data()])
            return colorWidget
        return None

class RunModel(QAbstractTableModel):
    ActiveRole = Qt.UserRole + 1

    def __init__(self, data, parent=None):
        super().__init__()
        self._data = data
        self.sortOrder = Qt.AscendingOrder
        self.header_labels = ['Load', 'Run ID', 'Plot', 'Colour']

    def update_data(self, data):
        self._data = data
        self.sort(1, self.sortOrder)

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return 4

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self._data[index.row()] if index.column() == 1 else None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.header_labels[section]
        return QAbstractTableModel.headerData(self, section, orientation, role)

    def sort(self, col, order=Qt.AscendingOrder):
        self.sortOrder = order
        oldIndexList = self.persistentIndexList()
        olddata = self._data[:]
        if order == Qt.AscendingOrder:
            self._data.sort()
        else:
            self._data.sort(reverse=True)
        newIndexList = [self.index(self._data.index(olddata[idx.row()]), idx.column(), idx.parent()) for idx in oldIndexList]
        self.changePersistentIndexList(oldIndexList, newIndexList)
        self.modelReset.emit()