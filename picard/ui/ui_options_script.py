# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'options_script.ui'
#
# Created: Thu Sep 14 21:17:34 2006
#      by: PyQt4 UI code generator 4.0
#          E:\projects\picard-qt\ui\compile.py
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(QtCore.QSize(QtCore.QRect(0,0,401,426).size()).expandedTo(Form.minimumSizeHint()))

        self.vboxlayout = QtGui.QVBoxLayout(Form)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.enable_tagger_script = QtGui.QGroupBox(Form)
        self.enable_tagger_script.setCheckable(True)
        self.enable_tagger_script.setObjectName("enable_tagger_script")

        self.vboxlayout1 = QtGui.QVBoxLayout(self.enable_tagger_script)
        self.vboxlayout1.setMargin(9)
        self.vboxlayout1.setSpacing(6)
        self.vboxlayout1.setObjectName("vboxlayout1")

        self.tagger_script = QtGui.QTextEdit(self.enable_tagger_script)

        font = QtGui.QFont(self.tagger_script.font())
        font.setFamily("Courier")
        font.setPointSize(8)
        font.setWeight(50)
        font.setItalic(False)
        font.setUnderline(False)
        font.setStrikeOut(False)
        font.setBold(False)
        self.tagger_script.setFont(font)
        self.tagger_script.setObjectName("tagger_script")
        self.vboxlayout1.addWidget(self.tagger_script)
        self.vboxlayout.addWidget(self.enable_tagger_script)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(_("Form"))
        self.enable_tagger_script.setTitle(_("Tagger Script"))