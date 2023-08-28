from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal, pyqtSlot

from ui.chart import Ui_Chart


class ChartForm(QtWidgets.QWidget):
#==================================

  def __init__(self, parent=None):
  #-------------------------------
    QtWidgets.QWidget.__init__(self, parent) # , QtCore.Qt.CustomizeWindowHint
#                                       | QtCore.Qt.WindowMinMaxButtonsHint
#                           #           | QtCore.Qt.WindowStaysOnTopHint
#                          )
    closekey = QtWidgets.QShortcut(QtGui.QKeySequence.Close, self, activated=self.close)
    self.ui = Ui_Chart()
    self.ui.setupUi(self)
    self.ui.chart.chartPosition.connect(self.on_chart_resize)
    self.ui.chart.updateTimeScroll.connect(self.position_timescroll)
    self.ui.timescroll.hide()

  def setTimeRange(self, start, duration):
  #---------------------------------------
    self.ui.chart.setTimeRange(start, duration)
    self.ui.chart.setTimeScroll(self.ui.timescroll)

  '''
  def setSemanticTags(self, tags):
  #-------------------------------
    self.ui.chart.setSemanticTags(tags)

  def setMarker(self, time):
  #-------------------------
    self.ui.chart.setMarker(time)

  def addSignalPlot(self, id, label, units, visible=True, data=None, ymin=None, ymax=None):
  #----------------------------------------------------------------------------------------
    self.ui.chart.addSignalPlot(id, label, units, visible=visible, data=data, ymin=ymin, ymax=ymax)

  def addEventPlot(self, id, label, mapping=lambda x: str(x), visible=True, data=None):
  #------------------------------------------------------------------------------------
    self.ui.chart.addEventPlot(id, label, mapping, visible=visible, data=data)

  def addAnnotation(self, id, start, end, text, tags, edit=False):
  #---------------------------------------------------------------
    self.ui.chart.addAnnotation(id, start, end, text, tags, edit)

  def deleteAnnotation(self, id):
  #------------------------------
    self.ui.chart.deleteAnnotation(id)

  @pyqtSlot(int, bool)
  def setPlotVisible(self, id, visible=True):
  #------------------------------------------
    self.ui.chart.setPlotVisible(id, visible)

  @pyqtSlot(int, int)
  def movePlot(self, from_id, to_id):
  #----------------------------------
    self.ui.chart.movePlot(from_id, to_id)

  @pyqtSlot(int)
  def plotSelected(self, row):
  #---------------------------
    self.ui.chart.plotSelected(row)

  def orderPlots(self, ids):
  #-------------------------
    self.ui.chart.orderPlots(ids)

  def resetAnnotations(self):
  #--------------------------
    self.ui.chart.resetAnnotations()

  def save_chart_as_png(self, filename):
  #-------------------------------------
    self.ui.chart.save_as_png(filename)
  '''

#  def resizeEvent(self, e):
#  #------------------------
#    self.setGeometry(QtCore.QRect(10, 25, self.width()-20, self.height() - 50))

  def on_timescroll_valueChanged(self, position):
  #----------------------------------------------
    self.ui.chart.moveTimeScroll(self.ui.timescroll)

  def position_timescroll(self, visible):
  #--------------------------------------
    self.ui.chart.setTimeScroll(self.ui.timescroll)
    self.ui.timescroll.setVisible(visible)

  '''
  def on_timezoom_currentIndexChanged(self, text):
  #-----------------------------------------------
    if isinstance(text, str) and text != "":
      scale = float(str(text).split()[0])
      self.ui.chart.setTimeZoom(scale)
      self.position_timescroll(scale > 1.0)

  @pyqtSlot(float)
  def zoom_chart(self, scale):
  #---------------------------
    if self.ui.timezoom.count() > self._user_zoom_index:
      self.ui.timezoom.setItemText(self._user_zoom_index, "%.2f x" % scale)
    else:
      self.ui.timezoom.insertItem(self._user_zoom_index, "%.2f x" % scale)
    self.ui.timezoom.setCurrentIndex(-1)
    self.ui.timezoom.setCurrentIndex(self._user_zoom_index)
    # Above will trigger on_timezoom_currentIndexChanged()
  '''

  @pyqtSlot(bool)
  def position_timescroll(self, visible):
  #--------------------------------------
    self.ui.chart.setTimeScroll(self.ui.timescroll)
    self.ui.timescroll.setVisible(visible)

  def on_frame_frameResize(self, geometry):
  #----------------------------------------
    geometry.adjust(3, 3, -3, -3)
    self.ui.chart.setGeometry(geometry)
    #QtCore.QRect(offset-4, self.height()-40, width+8, 30))

  @pyqtSlot(int, int, int)
  def on_chart_resize(self, offset, width, bottom):
  #------------------------------------------------
    h = self.ui.timescroll.height()
    self.ui.timescroll.setGeometry(QtCore.QRect(offset-10, bottom+27, width+40, h))

  def on_chart_customContextMenuRequested(self, pos):
  #--------------------------------------------------
    self.ui.chart.contextMenu(pos)



