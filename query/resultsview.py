import sys
import logging

from PyQt4 import QtCore, QtGui


class ResultsView(QtGui.QTableView):
#===================================

  def __init__(self, *args, **kwds):
  #---------------------------------
    QtGui.QTableView.__init__(self, *args, **kwds)
    self.horizontalHeader().setStretchLastSection(True)
    self.horizontalHeader().setHighlightSections(False)
    self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
    self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)

