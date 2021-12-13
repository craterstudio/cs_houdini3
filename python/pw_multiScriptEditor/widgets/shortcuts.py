from Qt import QtCore, QtWidgets, QtCompat

import shortcuts_UIs
import os

class shortcutsClass(QtWidgets.QDialog, shortcuts_UIs.Ui_Dialog):
    def __init__(self, parent):
        super(shortcutsClass, self).__init__(parent)
        self.setupUi(self)
        QtCompat.setSectionResizeMode(self.table.horizontalHeader(), QtWidgets.QHeaderView.Stretch)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(['Action', 'Shortcut'])
        self.read()

    def read(self):
        src = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'shortcuts.txt')
        if os.path.exists(src):
            self.label.hide()
            lines = open(src).readlines()
            for i, l in enumerate(lines):
                self.table.insertRow(self.table.rowCount())
                description, shortcut = l.split('>')
                item = QtWidgets.QTableWidgetItem(description)
                self.table.setItem(i, 0, item)
                item.setFlags(QtCore.Qt.ItemIsEnabled)
                item = QtWidgets.QTableWidgetItem(shortcut)
                item.setFlags(QtCore.Qt.ItemIsEnabled)
                self.table.setItem(i, 1, item)
        else:
            self.table.hide()
