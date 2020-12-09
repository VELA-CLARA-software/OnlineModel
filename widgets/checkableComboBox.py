from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class checkableComboBox(QComboBox):
    """A QComboBox where individual entried can be checked."""

    tagChanged = pyqtSignal()
    tagChecked = pyqtSignal(str)
    tagUnchecked = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        """Initialise the checkable combo-box."""
        super(checkableComboBox, self).__init__()
        self.view().clicked.connect(self.addRemoveTags)

    def addCheckableItem(self, item):
        """Add an item to the combo-box."""
        self.addItem(item)
        item = self.model().item(self.count()-1,0)
        item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        item.setCheckState(Qt.Unchecked)

    def itemChecked(self, index):
        """Return if the item at index is checked or not."""
        item = self.model().item(index,0)
        return item.checkState() == Qt.Checked

    def addRemoveTags(self, index):
        """Emit a signal based on whether the item at index is checked or not."""
        tag = self.model().item(index.row(),0).text()
        if self.itemChecked(index.row()):
            self.tagChecked.emit(tag)
        else:
            self.tagUnchecked.emit(tag)
        self.tagChanged.emit()

    def setTagState(self, tag, state):
        """Set the check-state of a specific tag in the combo-box."""
        if state == Qt.Unchecked or state == Qt.Checked:
            for i in range(self.count()):
                item = self.model().item(i-1,0)
                if item.text() == tag:
                    item.setCheckState(state)

    def setTagStates(self, checkedtags=[]):
        """Check specific tags based on a list."""
        for i in range(self.count()):
            item = self.model().item(i-1,0)
            if item is not None:
                if item.text() in checkedtags:
                    item.setCheckState(Qt.Checked)
                else:
                    item.setCheckState(Qt.Unchecked)

    def getTagText(self, index):
        """Return the tag value for a given index in the combo-box."""
        return self.model().item(index,0).text()

    def getCheckedTags(self, checkedtags=[]):
        """Return a list of all checked tags in the combo-box."""
        return [self.getTagText(i) for i in range(self.count()) if self.itemChecked(i)]
