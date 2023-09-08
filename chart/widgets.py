"""
Sub-class QT classes for widget promotion.


"""

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import pyqtSignal, pyqtSlot


class ChartFrame(QtWidgets.QFrame):
#==================================

  """
  Emit a signal when the size of the chart's frame changes.
  """

  frameResize = pyqtSignal(QtCore.QRect)

  def resizeEvent(self, e):
  #-----------------------
    self.frameResize.emit(self.geometry())

