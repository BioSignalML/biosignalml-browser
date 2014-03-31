"""
Sub-class QT classes for widget promotion.


"""

from PyQt5 import QtCore, QtWidgets


class ChartFrame(QtWidgets.QFrame):
#==================================

  """
  Emit a signal when the size of the chart's frame changes.
  """

  frameResize = QtCore.pyqtSignal(QtCore.QRect)

  def resizeEvent(self, e):
  #-----------------------
    self.frameResize.emit(self.geometry())

