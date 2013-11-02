# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\univtablesettingsdialog.ui'
#
# Created: Sat Nov  2 17:00:12 2013
#      by: PyQt4 UI code generator 4.10
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_UnivTableSettingsDialog(object):
    def setupUi(self, UnivTableSettingsDialog):
        UnivTableSettingsDialog.setObjectName(_fromUtf8("UnivTableSettingsDialog"))
        UnivTableSettingsDialog.resize(457, 261)
        self.verticalLayout_3 = QtGui.QVBoxLayout(UnivTableSettingsDialog)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.groupBox = QtGui.QGroupBox(UnivTableSettingsDialog)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.verticalLayout_4 = QtGui.QVBoxLayout(self.groupBox)
        self.verticalLayout_4.setObjectName(_fromUtf8("verticalLayout_4"))
        self.listWidgetHiddenColumns = QtGui.QListWidget(self.groupBox)
        self.listWidgetHiddenColumns.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.listWidgetHiddenColumns.setObjectName(_fromUtf8("listWidgetHiddenColumns"))
        self.verticalLayout_4.addWidget(self.listWidgetHiddenColumns)
        self.horizontalLayout.addWidget(self.groupBox)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.pushButtonMakeVisible = QtGui.QPushButton(UnivTableSettingsDialog)
        self.pushButtonMakeVisible.setObjectName(_fromUtf8("pushButtonMakeVisible"))
        self.verticalLayout.addWidget(self.pushButtonMakeVisible)
        self.pushButtonMakeHidden = QtGui.QPushButton(UnivTableSettingsDialog)
        self.pushButtonMakeHidden.setObjectName(_fromUtf8("pushButtonMakeHidden"))
        self.verticalLayout.addWidget(self.pushButtonMakeHidden)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.groupBox_2 = QtGui.QGroupBox(UnivTableSettingsDialog)
        self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.groupBox_2)
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.listWidgetVisibleColumns = QtGui.QListWidget(self.groupBox_2)
        self.listWidgetVisibleColumns.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.listWidgetVisibleColumns.setObjectName(_fromUtf8("listWidgetVisibleColumns"))
        self.horizontalLayout_2.addWidget(self.listWidgetVisibleColumns)
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.pushButtonMoveUp = QtGui.QPushButton(self.groupBox_2)
        self.pushButtonMoveUp.setObjectName(_fromUtf8("pushButtonMoveUp"))
        self.verticalLayout_2.addWidget(self.pushButtonMoveUp)
        self.pushButtonMoveDown = QtGui.QPushButton(self.groupBox_2)
        self.pushButtonMoveDown.setObjectName(_fromUtf8("pushButtonMoveDown"))
        self.verticalLayout_2.addWidget(self.pushButtonMoveDown)
        spacerItem2 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem2)
        self.horizontalLayout_2.addLayout(self.verticalLayout_2)
        self.horizontalLayout.addWidget(self.groupBox_2)
        self.verticalLayout_3.addLayout(self.horizontalLayout)
        self.buttonBox = QtGui.QDialogButtonBox(UnivTableSettingsDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout_3.addWidget(self.buttonBox)

        self.retranslateUi(UnivTableSettingsDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), UnivTableSettingsDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), UnivTableSettingsDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(UnivTableSettingsDialog)

    def retranslateUi(self, UnivTableSettingsDialog):
        UnivTableSettingsDialog.setWindowTitle(_translate("UnivTableSettingsDialog", "Table Settings", None))
        self.groupBox.setTitle(_translate("UnivTableSettingsDialog", "Hidden Columns", None))
        self.pushButtonMakeVisible.setText(_translate("UnivTableSettingsDialog", ">>", None))
        self.pushButtonMakeHidden.setText(_translate("UnivTableSettingsDialog", "<<", None))
        self.groupBox_2.setTitle(_translate("UnivTableSettingsDialog", "Visible Columns", None))
        self.pushButtonMoveUp.setText(_translate("UnivTableSettingsDialog", "Move Up", None))
        self.pushButtonMoveDown.setText(_translate("UnivTableSettingsDialog", "Move Down", None))

