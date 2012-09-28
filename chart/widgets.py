"""
Sub-class QT classes for widget promotion.


"""

from PyQt4 import QtCore, QtGui


class ChartFrame(QtGui.QFrame):
#==============================

  """
  Emit a signal when the size of the chart's frame changes.
  """

  frameResize = QtCore.pyqtSignal(QtCore.QRect)

  def resizeEvent(self, e):
  #-----------------------
    self.frameResize.emit(self.geometry())

