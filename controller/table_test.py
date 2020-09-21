from PyQt5 import QtCore, QtGui, QtWidgets
import re

class LoadButtonDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner

    def paint(self, painter, option, index):
        if isinstance(self.parent(), QtWidgets.QAbstractItemView):
            self.parent().openPersistentEditor(index)
        super(LoadButtonDelegate, self).paint(painter, option, index)

    def createEditor(self, parent, option, index):
        editor = QtWidgets.QPushButton(self.get_id(index), parent)
        # editor.clicked.connect(self.commit_editor)
        return editor

    def get_id(self, index):
        self.owner.model()._data[index.row()]

class PlotCheckboxDelegate(LoadButtonDelegate):

    def createEditor(self, parent, option, index):
        editor = QtWidgets.QCheckBox(self.get_id(index), parent)
        # editor.clicked.connect(self.commit_editor)
        return editor

class Model(QtCore.QAbstractTableModel):
    ActiveRole = QtCore.Qt.UserRole + 1
    def __init__(self, data, parent=None):
        super().__init__()
        self._data = data

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 4

    # def flags(self, index):
    #     return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def data(self, index, role):
        if not index.isValid():
            return QtCore.QVariant()
        elif role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        return QtCore.QVariant(self._data[index.row()]) if index.column() < 3 else None

class Main(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        # create table view:
        self.get_choices_data()
        self.get_table_data()
        self.tableview = self.createTable()

        # Set the maximum value of row to the selected row
        self.selectrow = self.tableview.model().rowCount()

        # create gridlayout
        grid_layout = QtWidgets.QGridLayout()
        grid_layout.addWidget(self.tableview, 1, 0, 1, 7)

        # initializing layout
        self.title = 'Data Visualization Tool'
        self.setWindowTitle(self.title)
        self.setGeometry(0, 0, 1024, 576)
        self.showMaximized()
        self.centralwidget = QtWidgets.QWidget()
        self.centralwidget.setLayout(grid_layout)
        self.setCentralWidget(self.centralwidget)

    def get_table_data(self):
        # set initial table values:
        self.tabledata = ['1','2','3']

    def get_choices_data(self):
        # set combo box choices:
        self.choices = ['type_1', 'type_2', 'type_3', 'type_4', 'type_5']

    def createTable(self):
        tv = QtWidgets.QTableView()
        # set header for columns:
        header = ['Name', 'Type', 'var1', 'var2', 'var3']

        tablemodel = Model(self.tabledata, self)
        tv.setModel(tablemodel)
        hh = tv.horizontalHeader()
        tv.resizeRowsToContents()
        # ItemDelegate for combo boxes
        tv.setItemDelegateForColumn(0, LoadButtonDelegate(tv))
        tv.setItemDelegateForColumn(2, PlotCheckboxDelegate(tv))
        return tv


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    main = Main()
    main.show()
    sys.exit(app.exec_())
