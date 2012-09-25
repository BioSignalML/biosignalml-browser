import sys
import logging

from PyQt4 import QtCore, QtGui

from chart import Ui_Form

import biosignalml.formats.hdf5 as hdf5
import biosignalml.formats.edf  as edf



class ChartForm(QtGui.QWidget):
#==============================

  def __init__(self, start, duration, parent=None):
  #------------------------------------------------
    QtGui.QWidget.__init__(self, parent)
    self.ui = Ui_Form()
    self.ui.setupUi(self)
    self.ui.chart.chartPosition.connect(self.on_chart_resize)
    self.ui.timescroll.hide()
    self.ui.chart.setTimeRange(start, duration)


  def addSignalPlot(self, label, units, data=None, ymin=None, ymax=None):
  #----------------------------------------------------------------------
    return self.ui.chart.addSignalPlot(label, units, data=data, ymin=ymin, ymax=ymax)

  def addEventPlot(self, label, mapping=lambda x: str(x), data=None):
  #----------------------------------------------------------------
    return self.ui.chart.addEventPlot(label, mapping, data=data)

  def save_chart_as_png(self, filename):
  #-------------------------------------
    self.ui.chart.save_as_png(filename)

  def resizeEvent(self, e):
  #------------------------
    self.ui.layoutWidget.setGeometry(QtCore.QRect(10, 25, self.width()-20, self.height() - 50))

  def on_timescroll_valueChanged(self, position):
  #----------------------------------------------
    self.ui.chart.moveTimeScroll(self.ui.timescroll)

  def on_timezoom_currentIndexChanged(self, index):
  #------------------------------------------------
    if isinstance(index, int):
      scale = [1.0, 2.0, 5.0, 10.0][index]
      self.ui.chart.setTimeZoom(scale)
      self.ui.chart.setTimeScroll(self.ui.timescroll)
      self.ui.timescroll.setVisible(index > 0)

  def on_frame_frameResize(self, geometry):
  #----------------------------------------
    geometry.adjust(3, 3, -3, -3)
    self.ui.chart.setGeometry(geometry)
    #QtCore.QRect(offset-4, self.height()-40, width+8, 30))

  def on_chart_resize(self, offset, width, bottom):
  #------------------------------------------------
    h = self.ui.timescroll.height()
    self.ui.timescroll.setGeometry(QtCore.QRect(offset-10, bottom+27, width+40, h))

  def on_chart_customContextMenuRequested(self, pos):
  #--------------------------------------------------
    self.ui.chart.contextMenu(pos)


if __name__ == "__main__":
#=========================

  def wfdbAnnotation(e):
  #---------------------
    import wfdb
    mark = wfdb.annstr(int(e))
    ##  text = "Pacing on" if t < 100 else "Pacing off"   ########
    ##  chart.annotate(text, t, 0.0, textpos=(t, 1.05))
    if mark in "NLRBAaJSVrFejnE/fQ?":
      if mark == 'N': mark = u'\u2022'  # Unicode bullet
      return (mark, wfdb.anndesc(int(e)))
    return ('', '')

  logging.basicConfig(format='%(asctime)s: %(message)s')
  logging.getLogger().setLevel('DEBUG')

  app = QtGui.QApplication(sys.argv)

  start = 90
  duration = 20
  viewer1 = ChartForm(start, duration)
  record1 = 'mitdb/102'
  rec1 = hdf5.HDF5Recording.open('/physiobank/database/%s.h5' % record1)
  for n, s in enumerate(rec1.signals()):
    if s.rate:                  ###### Need attribute for Signal
      label = "V5" if n == 0 else "V2" if n == 1 else "S%d" % n  #########
      units = "mV"
      p = viewer1.addSignalPlot(label, units)
    else:                       ###### or Annotation...
      label = 'atr'   ##########
      p = viewer1.addEventPlot(label, wfdbAnnotation)
    for d in s.read(rec1.interval(start, duration)): p.addData(d) 
  viewer1.show()

  #viewer1.save_chart_as_png('test.png')   ## Needs to be via 'Save' button/menu and file dialog...

  viewer1.raise_()

  start = 100
  duration = 500
  viewer2 = ChartForm(start, duration)
  record2 = 'swa49.edf'
  rec2 = edf.EDFRecording.open('/Users/dave/biosignalml/testdata/%s' % record2)
  for n, s in enumerate(rec2.signals()):
    if 17 <= n and s.rate:
      logging.debug("Adding plot for %s", s.label)
      p = viewer2.addSignalPlot(s.label, s.units, ymin=s.minValue, ymax=s.maxValue)
      for d in s.read(rec2.interval(start, duration)): p.addData(d) 
  viewer2.show()
  viewer2.raise_()

  sys.exit(app.exec_())
