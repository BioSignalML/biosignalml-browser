# -*- coding: utf-8 -*-

# Modified from form generated from 'ui/mainwindow.ui'
#
# Created: Wed Aug 26 10:24:57 2015
#      by: PyQt5 UI code generator 5.4
#
from PyQt6 import QtCore, QtGui, QtWidgets

from chartform import ChartForm



class Ui_MainWindow(object):
#===========================

    def setupUi(self, MainWindow, signalsWidget, annotationsWidget, scrollWidget):
    #-----------------------------------------------------------------------------
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1275, 800)
        MainWindow.setDockNestingEnabled(False)

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.chartform = ChartForm(self.centralwidget)
        self.chartform.setObjectName("chartform")
        self.verticalLayout.addWidget(self.chartform)
        MainWindow.setCentralWidget(self.centralwidget)

        self.signalsDock = QtWidgets.QDockWidget(MainWindow)
        self.signalsDock.setFloating(False)
        self.signalsDock.setAllowedAreas(QtCore.Qt.DockWidgetArea.AllDockWidgetAreas)
        self.signalsDock.setObjectName("signalsDock")
        self.signalsWidget = signalsWidget
        self.signalsWidget.setObjectName("signalsWidget")
        self.signalsDock.setWidget(self.signalsWidget)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self.signalsDock)
        
        self.annotationsDock = QtWidgets.QDockWidget(MainWindow)
        self.annotationsDock.setFloating(False)
        self.signalsDock.setAllowedAreas(QtCore.Qt.DockWidgetArea.AllDockWidgetAreas)
        self.annotationsDock.setObjectName("annotationsDock")
        self.annotationsWidget = annotationsWidget
        self.annotationsWidget.setObjectName("annotationsWidget")
        self.annotationsDock.setWidget(self.annotationsWidget)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea.TopDockWidgetArea, self.annotationsDock)

        self.scrollDock = QtWidgets.QDockWidget(MainWindow)
        self.scrollDock.setFloating(False)
        self.scrollDock.setAllowedAreas(QtCore.Qt.DockWidgetArea.TopDockWidgetArea
                                      | QtCore.Qt.DockWidgetArea.BottomDockWidgetArea)
        self.scrollDock.setObjectName("scrollDock")
        self.scrollWidget = scrollWidget
        self.scrollWidget.setObjectName("scrollWidget")
        self.scrollDock.setWidget(self.scrollWidget)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea.BottomDockWidgetArea, self.scrollDock)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)


    def retranslateUi(self, MainWindow):
    #-----------------------------------
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
