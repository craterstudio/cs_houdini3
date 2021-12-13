# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/johannes/PycharmProjects/pw_MultiScriptEditor/pw_multiScriptEditor/widgets/shortcuts.ui'
#
# Created: Sat Apr 28 00:29:02 2018
#      by: pyside2-uic  running on PySide2 5.9.0a1.dev1524638381
#
# WARNING! All changes made in this file will be lost!

from Qt import QtGui, QtCore, QtCompat, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(573, 391)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.table = QtWidgets.QTableWidget(Dialog)
        self.table.setObjectName("table")
        self.table.setColumnCount(0)
        self.table.setRowCount(0)
        self.verticalLayout.addWidget(self.table)
        self.label = QtWidgets.QLabel(Dialog)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setWeight(75)
        font.setItalic(False)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.label.setTextFormat(QtCore.Qt.AutoText)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtCompat.translate("Dialog", "Shortcuts list", None, -1))
        self.label.setText(QtCompat.translate("Dialog", "Shortcut list hot found!!!", None, -1))

