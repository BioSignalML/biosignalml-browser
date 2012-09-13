import sys
from PyQt4 import QtCore, QtGui

from term import Ui_QueryTerm



class QueryTerm(QtGui.QWidget):
#==============================

  def __init__(self, parent=None):
  #-------------------------------
    QtGui.QWidget.__init__(self, parent)
    self.ui = Ui_QueryTerm()
    self.ui.setupUi(self)

    self.ui.property.addItem("Text")
    self.ui.property.addItem("Property")

    self.ui.relation.hide()
    self.ui.valuelist.hide()
    self.ui.valuetext.hide()
    self.ui.property.currentIndexChanged.connect(self.on_property_changed)
    self.ui.operation.currentIndexChanged.connect(parent.add_term)

  def hide_operation(self):
  #-----------------------
    self.ui.operation.hide()

  def show_operation(self):    ## Won't be used ??
  #-----------------------
    self.ui.operation.show()

  def on_property_changed(self, index):
  #------------------------------------
    self.ui.relation.clear()
    self.ui.relation.addItem("equal")
    self.ui.relation.addItem("not equal")
    self.ui.relation.setVisible(index > 0)

    self.ui.valuetext.setVisible(index > 0)   ## Or value text

