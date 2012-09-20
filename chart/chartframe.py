from PyQt4 import QtCore, QtGui


class ChartFrame(QtGui.QFrame):
#==============================

  frameResize = QtCore.pyqtSignal(QtCore.QRect)

  def resizeEvent(self, e):
  #-----------------------
    self.frameResize.emit(self.geometry())

