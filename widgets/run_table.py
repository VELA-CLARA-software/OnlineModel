import datetime
from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex, QVariant, QEvent
from PyQt5.QtWidgets import QStyledItemDelegate, QItemDelegate, QAbstractItemView, QPushButton, QCheckBox
import pyqtgraph as pg

class LoadButtonDelegate(QStyledItemDelegate):
    """
    A delegate that places a fully functioning QPushButton cell of the column to which it's applied.
    """
    def __init__(self, owner, rpc):
        super().__init__(owner)
        self.owner = owner
        self.rpc = rpc

    def paint(self, painter, option, index):
        """
        Paint a "load" pushbutton.
        """
        if isinstance(self.parent(), QAbstractItemView):
            self.parent().openPersistentEditor(index)
        super().paint(painter, option, index)

    def createEditor(self, parent, option, index):
        """Create the pushbutton and connect it to the load signal."""
        loadButton = QPushButton('Load', parent)
        loadButton.clicked.connect(lambda: self.rpc.load_yaml_from_db(self.get_id(index)))
        return loadButton

    def get_id(self, index):
        """Get the run ID of the current row."""
        return self.owner.model().get_run_id(index.row())

class PlotCheckboxDelegate(QItemDelegate):
    """
    A delegate that places a fully functioning QCheckBox cell of the column to which it's applied.
    """
    def __init__(self, parent, rpc):
        super().__init__(parent)
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
        """Get the run ID of the current row."""
        return self.owner.model().get_run_id(index.row())

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
    """
    A delegate that places a plot colorWidget cell of the column to which it's applied.
    """
    def createEditor(self, parent, option, index):
        """Create the plot color widget."""
        # print(index.row(), index.siblingAtColumn(1).data(), index.siblingAtColumn(1).data() in self.rpc.run_plots)
        if index.siblingAtColumn(1).data() in self.rpc.run_plots:
            colorWidget = pg.ColorButton(parent)
            colorWidget.setEnabled(False)
            colorWidget.setColor(self.rpc.run_plot_colors[index.siblingAtColumn(1).data()])
            return colorWidget
        return None

class DateDelegate(QStyledItemDelegate):
    """
    A delegate that returns a date formatted string cell of the column to which it's applied.
    """
    def displayText(self, text, locale):
        """Return date formatted string."""
        return datetime.datetime.fromtimestamp(float(text)).strftime('%d-%m-%Y %H:%M:%S')

class RunModel(QAbstractTableModel):
    """QAbstractTableModel for storing run IDs and timestamps."""

    ActiveRole = Qt.UserRole + 1

    def __init__(self, data, timestamps=None, rpc=None, parent=None):
        """Initialise the table model object."""
        super().__init__()
        self._data = data
        self._timestamps = timestamps
        self.currentSortColumn = 4
        self.currentSortDirection = Qt.AscendingOrder
        self.header_labels = ['Load', 'Run ID', 'Plot', 'Colour', 'Timestamp']

    def get_run_id(self, row):
        """Return the correct row from the data object."""
        return self._data[row]

    def update_data(self, data, timestamps):
        """Update the run ID and timestamp data objects, and re-sort the data."""
        self._data = data
        self._timestamps = timestamps
        self.sort(self.currentSortColumn, self.currentSortDirection)

    def rowCount(self, parent=QModelIndex()):
        """Return the number of rows, which is equal to the length of the run ID object."""
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        """Return the number of columns, which is equal to the length of the header labels."""
        return len(self.header_labels)

    def sort(self, column=None, direction=0):
        """
            Sort the run ID and timestamp data objects.
            - only able to sort if column = 4 (timestamp) or coumn = 1 (run ID) for now.
            - Direction=0 -> ASCENDING
            - Direction=1 -> DESCENDING
        """

        self.layoutAboutToBeChanged.emit()
        self.currentSortDirection = direction
        if column == 1:
            self.currentSortColumn = 1
            self._data=sorted(self._data, reverse=(not direction))
            self.modelReset.emit()
        if column == 4:
            self.currentSortColumn = 4
            self._timestamps=dict(sorted(self._timestamps.items(), key=lambda x: x[1],reverse=(not direction)))
            self._data = list(self._timestamps.keys())
            self.modelReset.emit()

    def data(self, index, role):
        """Return the correct data for a given row-column index."""
        if role == Qt.DisplayRole:
            if index.column() == 1:
                return QVariant(self._data[index.row()])
            if index.column() == 4:
                return QVariant(self._timestamps[self._data[index.row()]])
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Return the header data based on the header labels defined."""
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.header_labels[section]
        return QAbstractTableModel.headerData(self, section, orientation, role)
