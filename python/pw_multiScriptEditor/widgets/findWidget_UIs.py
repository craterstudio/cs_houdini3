# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/johannes/PycharmProjects/pw_MultiScriptEditor/pw_multiScriptEditor/widgets/findWidget.ui'
#
# Created: Sat Apr 28 00:29:02 2018
#      by: pyside2-uic  running on PySide2 5.9.0a1.dev1524638381
#
# WARNING! All changes made in this file will be lost!

from Qt import QtCore, QtCompat, QtWidgets

class Ui_findReplace(object):
    def setupUi(self, findReplace):
        findReplace.setObjectName("findReplace")
        findReplace.resize(246, 101)
        self.verticalLayout = QtWidgets.QVBoxLayout(findReplace)
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.replace_le = QtWidgets.QLineEdit(findReplace)
        self.replace_le.setObjectName("replace_le")
        self.gridLayout.addWidget(self.replace_le, 1, 0, 1, 1)
        self.find_le = QtWidgets.QLineEdit(findReplace)
        self.find_le.setObjectName("find_le")
        self.gridLayout.addWidget(self.find_le, 0, 0, 1, 1)
        self.find_btn = QtWidgets.QPushButton(findReplace)
        self.find_btn.setObjectName("find_btn")
        self.gridLayout.addWidget(self.find_btn, 0, 1, 1, 1)
        self.replace_btn = QtWidgets.QPushButton(findReplace)
        self.replace_btn.setObjectName("replace_btn")
        self.gridLayout.addWidget(self.replace_btn, 1, 1, 1, 1)
        self.replaceAll_btn = QtWidgets.QPushButton(findReplace)
        self.replaceAll_btn.setObjectName("replaceAll_btn")
        self.gridLayout.addWidget(self.replaceAll_btn, 2, 1, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)

        self.retranslateUi(findReplace)
        QtCore.QMetaObject.connectSlotsByName(findReplace)
        findReplace.setTabOrder(self.find_le, self.replace_le)
        findReplace.setTabOrder(self.replace_le, self.find_btn)
        findReplace.setTabOrder(self.find_btn, self.replace_btn)
        findReplace.setTabOrder(self.replace_btn, self.replaceAll_btn)

    def retranslateUi(self, findReplace):
        findReplace.setWindowTitle(QtCompat.translate("findReplace", "Find and Replace", None, -1))
        self.find_btn.setText(QtCompat.translate("findReplace", "Find", None, -1))
        self.replace_btn.setText(QtCompat.translate("findReplace", "Replace", None, -1))
        self.replaceAll_btn.setText(QtCompat.translate("findReplace", "Replace All", None, -1))

