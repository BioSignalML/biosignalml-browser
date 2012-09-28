import sys
import logging

from PyQt4 import QtCore, QtGui

from ui.chart      import Ui_Chart
from ui.controller import Ui_Controller

import biosignalml.formats.hdf5 as hdf5
import biosignalml.formats.edf  as edf



class ChartForm(QtGui.QWidget):
#==============================

  def __init__(self, start, duration, parent=None):
  #------------------------------------------------
    QtGui.QWidget.__init__(self, parent)
    self.ui = Ui_Chart()
    self.ui.setupUi(self)
    self.ui.chart.chartPosition.connect(self.on_chart_resize)
    self.ui.timescroll.hide()
    self.ui.chart.setTimeRange(start, duration)


  def addSignalPlot(self, id, label, units, visible=True, data=None, ymin=None, ymax=None):
  #----------------------------------------------------------------------------------------
    self.ui.chart.addSignalPlot(id, label, units, visible=visible, data=data, ymin=ymin, ymax=ymax)

  def addEventPlot(self, id, label, mapping=lambda x: str(x), visible=True, data=None):
  #------------------------------------------------------------------------------------
    self.ui.chart.addEventPlot(id, label, mapping, visible=visible, data=data)

  def appendData(self, id, data):
  #------------------------------
    self.ui.chart.appendData(id, data)

  def setPlotVisible(self, id, visible=True):
  #------------------------------------------
    self.ui.chart.setVisible(id, visible)

  def orderPlots(self, ids):
  #-------------------------
    self.ui.chart.orderPlots(ids)

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



class SignalInfo(QtCore.QAbstractTableModel):
#============================================

  HEADER = [ '', 'Label', 'Uri' ]

  def __init__(self, *args, **kwds):
  #---------------------------------
    QtCore.QAbstractTableModel.__init__(self, *args, **kwds)
    self._rows = [ [True,  'Signal 1', 'http://example.org/signal/1'],
                   [True,  'Signal 2', 'http://example.org/signal/2'],
                   [False, 'Signal 3', 'http://example.org/signal/3'],
                   [True,  'Signal 4', 'http://example.org/signal/4'],
                 ]

  def rowCount(self, parent=None):
  #-------------------------------
    return len(self._rows)

  def columnCount(self, parent=None):
  #----------------------------------
    return len(self.HEADER)

  def headerData(self, section, orientation, role):
  #------------------------------------------------
    if role == QtCore.Qt.DisplayRole:
      if orientation == QtCore.Qt.Horizontal:
        return self.HEADER[section]

  def data(self, index, role):
  #---------------------------
    if   role == QtCore.Qt.DisplayRole:
      if index.column() != 0:
        return self._rows[index.row()][index.column()]
      else:
        return QtCore.QVariant()
    elif role == QtCore.Qt.CheckStateRole:
      if index.column() == 0:
        return QtCore.Qt.Checked if self._rows[index.row()][0] else QtCore.Qt.Unchecked

  def setData(self, index, value, role):
  #-------------------------------------
    if role == QtCore.Qt.CheckStateRole and index.column() == 0:
      self._rows[index.row()][0] = (value == QtCore.Qt.Checked)
      self.dataChanged.emit(index, index)
      return True
    return False

  def moveRow(self, sourceindex, sourcerow, destindex, destrow):
  #-------------------------------------------------------------
    data = self._rows[sourcerow]
    if sourcerow > destrow:        # Moving up
      self._rows[destrow+1:sourcerow+1] = self._rows[destrow:sourcerow]
      self._rows[destrow] = data
    elif (sourcerow+1) < destrow:  # Moving down
      self._rows[sourcerow:destrow-1] = self._rows[sourcerow+1:destrow]
      self._rows[destrow-1] = data

  def flags(self, index):
  #-----------------------
    if index.column() == 0:
      return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsSelectable
    else:
      return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable



class Controller(QtGui.QWidget):
#===============================

  def __init__(self, recording, start, duration, order=None, parent=None):
  #-----------------------------------------------------------------------
    QtGui.QWidget.__init__(self, parent)
    self.controller = Ui_Controller()
    self.controller.setupUi(self)
    self.controller.signals.setModel(SignalInfo(recording, order))


    self.viewer = ChartForm(start, duration, self)

    # Connect with signals/slots....

    for n, s in enumerate(recording.signals()):
      if s.rate:                  ###### Need attribute for Signal
        label = "V5" if n == 0 else "V2" if n == 1 else "S%d" % n  #########
        units = "mV"
        self.viewer.addSignalPlot(n, label, units)
      else:                       ###### or Annotation...
        label = 'atr'   ##########
        self.viewer.addEventPlot(n, label, wfdbAnnotation)

      for d in s.read(recording.interval(start, duration)):
        self.viewer.appendData(n, d)

   self.viewer.orderPlots(order if order else [])  # via controller??



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


  record1 = 'mitdb/102'
  rec1 = hdf5.HDF5Recording.open('/physiobank/database/%s.h5' % record1)
  ctl1 = Controller(rec1, 90, 20, [0, 2, 1])
  ctl1.show()
  ctl1.raise_()

  """
  record1 = 'mitdb/102'
  rec1 = hdf5.HDF5Recording.open('/physiobank/database/%s.h5' % record1)
  for n, s in enumerate(rec1.signals()):
    if s.rate:                  ###### Need attribute for Signal
      label = "V5" if n == 0 else "V2" if n == 1 else "S%d" % n  #########
      units = "mV"
      viewer1.addSignalPlot(n, label, units)
    else:                       ###### or Annotation...
      label = 'atr'   ##########
      viewer1.addEventPlot(n, label, wfdbAnnotation)
    for d in s.read(rec1.interval(start, duration)):
      viewer1.appendData(n, d)

  viewer1.orderPlots([0, 2, 1])
  viewer1.show()

  #viewer1.save_chart_as_png('test.png')   ## Needs to be via 'Save' button/menu and file dialog...

  """


  """
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
  """
  sys.exit(app.exec_())
