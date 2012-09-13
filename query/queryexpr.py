import sys
from PyQt4 import QtCore, QtGui

from expr import Ui_QueryExpr
from queryterm import QueryTerm



class QueryExpr(QtGui.QWidget):
#==============================

  def __init__(self, parent=None):
  #-------------------------------
    QtGui.QWidget.__init__(self, parent)
    self.ui = Ui_QueryExpr()
    self.ui.setupUi(self)
    self.terms = [ self.ui.term ]

  def new_term(self):
  #------------------
    term = QueryTerm(self)
    self.terms.append(term)
    self.ui.termsLayout.addWidget(term)
    self.update()


  def hide_operation(self):
  #-----------------------
    self.ui.operation.hide()

  def show_operation(self):    ## Won't be used ??
  #-----------------------
    self.ui.operation.show()


  def add_term(self, operation):
  #-----------------------------
    # Only when operation was 0 --> > 0
    if operation > 0:
      self.new_term()
