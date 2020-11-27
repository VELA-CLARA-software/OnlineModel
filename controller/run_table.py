from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import pyqtgraph as pg
from copy import copy
import datetime
#datetime.datetime.fromtimestamp(float(timestamp)).strftime('%d-%m-%Y %H:%M:%S')

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
        return self.owner.model()._data[index.row()]

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

class DateDelegate(QStyledItemDelegate):

    def __init__(self, owner, rpc):
        super(DateDelegate, self).__init__(owner)
        self.owner = owner
        self.rpc = rpc

    def displayText(self, text, locale):
        data = datetime.datetime.fromtimestamp(float(text)).strftime('%d-%m-%Y %H:%M:%S')
        return data

    def get_id(self, index):
        return self.owner.model()._timestamps[index.row()]

class RunModel(QAbstractTableModel):
    ActiveRole = Qt.UserRole + 1

    def __init__(self, data, timestamps=None, rpc=None, parent=None):
        super().__init__()
        self._data = data
        self._timestamps = timestamps
        self.currentSortDirection = Qt.AscendingOrder
        self.header_labels = ['Load', 'Run ID', 'Plot', 'Colour', 'Timestamp']

    def update_data(self, data, timestamps):
        self._data = data
        self._timestamps = timestamps
        self.sort(4, self.currentSortDirection)

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
        if column == 1:
            self._data=sorted(self._data, reverse=(not direction))
            # self._timestamps = {k:self._timestamps[k] for k in self._data.keys()}
            self.modelReset.emit()
        if column == 4:
            # self._rpc.emit_sort_by_timestamp_signal(column, direction)
            self._timestamps=dict(sorted(self._timestamps.items(), key=lambda x: x[1],reverse=(not direction)))
            self._data = list(self._timestamps.keys())
            self.modelReset.emit()
        # print('SORT CALLED on column: ', column)
        # print('SORT ORDER: ', direction)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            if index.column() == 1:
                return QVariant(self._data[index.row()])
            elif index.column() == 4:
                return QVariant(self._timestamps[self._data[index.row()]])
            else:
                return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.header_labels[section]
        return QAbstractTableModel.headerData(self, section, orientation, role)
