import sys
import logging

from PyQt4 import QtCore, QtGui

from ui.chart      import Ui_Chart
from ui.controller import Ui_Controller

import biosignalml.formats.hdf5 as hdf5
import biosignalml.formats.edf  as edf
import biosignalml.units.ontology as uom

from nrange import NumericRange
def wfdbAnnotation(e):
#=====================
  import wfdb
  mark = wfdb.annstr(int(e))
  ##  text = "Pacing on" if t < 100 else "Pacing off"   ########
  ##  chart.annotate(text, t, 0.0, textpos=(t, 1.05))
  if mark in "NLRBAaJSVrFejnE/fQ?":
    if mark == 'N': mark = u'\u2022'  # Unicode bullet
    return (mark, wfdb.anndesc(int(e)))
  return ('', '')



def signal_uri(signal):
#======================
  prefix = str(signal.recording.uri)
  uri = str(signal.uri)
  if uri.startswith(prefix): return uri[len(prefix):]
  else:                      return uri


class ChartForm(QtGui.QWidget):
#==============================

  def __init__(self, start, duration, parent=None):
  #------------------------------------------------
    QtGui.QWidget.__init__(self, parent)
    self.ui = Ui_Chart()
    self.ui.setupUi(self)
    self.ui.chart.chartPosition.connect(self.on_chart_resize)
    self.ui.chart.updateTimeScroll.connect(self.position_timescroll)
    self.ui.timescroll.hide()
    self.setTimeRange(start, duration)

  def setTimeRange(self, start, duration):
  #---------------------------------------
    self.ui.chart.setTimeRange(start, duration)
    self.ui.chart.setTimeScroll(self.ui.timescroll)

  def addSignalPlot(self, id, label, units, visible=True, data=None, ymin=None, ymax=None):
  #----------------------------------------------------------------------------------------
    self.ui.chart.addSignalPlot(id, label, units, visible=visible, data=data, ymin=ymin, ymax=ymax)

  def addEventPlot(self, id, label, mapping=lambda x: str(x), visible=True, data=None):
  #------------------------------------------------------------------------------------
    self.ui.chart.addEventPlot(id, label, mapping, visible=visible, data=data)

  def appendPlotData(self, id, data):
  #----------------------------------
    self.ui.chart.appendData(id, data)

  def setPlotVisible(self, id, visible=True):
  #------------------------------------------
    self.ui.chart.setPlotVisible(id, visible)

  def orderPlots(self, ids):
  #-------------------------
    self.ui.chart.orderPlots(ids)

  def movePlot(self, from_id, to_id):
  #----------------------------------
    self.ui.chart.movePlot(from_id, to_id)

  def plotSelected(self, row):
  #---------------------------
    self.ui.chart.plotSelected(row)

  def resetPlots(self):
  #--------------------
    self.ui.chart.resetPlots()

  def save_chart_as_png(self, filename):
  #-------------------------------------
    self.ui.chart.save_as_png(filename)

  def resizeEvent(self, e):
  #------------------------
    self.ui.layoutWidget.setGeometry(QtCore.QRect(10, 25, self.width()-20, self.height() - 50))

  def on_timescroll_valueChanged(self, position):
  #----------------------------------------------
    self.ui.chart.moveTimeScroll(self.ui.timescroll)

  def position_timescroll(self, visible):
  #--------------------------------------
    self.ui.chart.setTimeScroll(self.ui.timescroll)
    self.ui.timescroll.setVisible(visible)

  def on_timezoom_currentIndexChanged(self, index):
  #------------------------------------------------
    if isinstance(index, int):
      scale = [1.0, 2.0, 5.0, 10.0][index]
      self.ui.chart.setTimeZoom(scale)
      self.position_timescroll(index > 0)

  def position_timescroll(self, visible):
  #--------------------------------------
    self.ui.chart.setTimeScroll(self.ui.timescroll)
    self.ui.timescroll.setVisible(visible)

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

  rowVisible = QtCore.pyqtSignal(str, bool)   # id, state
  rowMoved = QtCore.pyqtSignal(str, str)      # from_id, to_id

  HEADER    = [ '', 'Label', 'Uri' ]
  ID_COLUMN = 2                               # Uri is ID


  def __init__(self, recording, *args, **kwds):
  #--------------------------------------------
    QtCore.QAbstractTableModel.__init__(self, *args, **kwds)
    self._rows = [ [True, s.label, signal_uri(s)]
                     for n, s in enumerate(recording.signals()) ]


  def rowCount(self, parent=None):
  #-------------------------------
    return len(self._rows)

  def columnCount(self, parent=None):
  #----------------------------------
    return len(self.HEADER)

  def headerData(self, section, orientation, role):
  #------------------------------------------------
    if orientation == QtCore.Qt.Horizontal:
      if role == QtCore.Qt.DisplayRole:
        return self.HEADER[section]
      elif role == QtCore.Qt.TextAlignmentRole:
        return QtCore.Qt.AlignLeft
      elif role == QtCore.Qt.FontRole:
        font = QtGui.QFont(QtGui.QApplication.font())
        font.setBold(True)
        return font

  def data(self, index, role):
  #---------------------------
    if   role == QtCore.Qt.DisplayRole:
      if index.column() != 0:
        return str(self._rows[index.row()][index.column()])
      else:
        return QtCore.QVariant()
    elif role == QtCore.Qt.CheckStateRole:
      if index.column() == 0:
        return QtCore.Qt.Checked if self._rows[index.row()][0] else QtCore.Qt.Unchecked

  def setData(self, index, value, role):
  #-------------------------------------
    if role == QtCore.Qt.CheckStateRole and index.column() == 0:
      self._rows[index.row()][0] = (value == QtCore.Qt.Checked)
      self.rowVisible.emit(self._rows[index.row()][self.ID_COLUMN], (value == QtCore.Qt.Checked))
      self.dataChanged.emit(index, index)
      return True
    return False

  def moveRow(self, sourceindex, sourcerow, destindex, destrow):
  #-------------------------------------------------------------
    data = self._rows[sourcerow]
    from_id = data[self.ID_COLUMN]
    if sourcerow > destrow:        # Moving up
      to_id = self._rows[destrow][self.ID_COLUMN]
      self._rows[destrow+1:sourcerow+1] = self._rows[destrow:sourcerow]
      self._rows[destrow] = data
    elif (sourcerow+1) < destrow:  # Moving down
      to_id = self._rows[destrow-1][self.ID_COLUMN]
      self._rows[sourcerow:destrow-1] = self._rows[sourcerow+1:destrow]
      self._rows[destrow-1] = data
    self.rowMoved.emit(from_id, to_id)

  def flags(self, index):
  #-----------------------
    if index.column() == 0:
      return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsSelectable
    else:
      return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

  def setVisibility(self, visible):
  #--------------------------------
    for r in xrange(len(self._rows)):
      self.setData(self.createIndex(r, 0),
                   QtCore.Qt.Checked if visible else QtCore.Qt.Unchecked,
                   QtCore.Qt.CheckStateRole)


class Controller(QtGui.QWidget):
#===============================

  def __init__(self, store, rec_uri, start, duration, parent=None):
  #----------------------------------------------------------------
    QtGui.QWidget.__init__(self, parent, QtCore.Qt.CustomizeWindowHint
                                       | QtCore.Qt.WindowMinMaxButtonsHint
                           #           | QtCore.Qt.WindowStaysOnTopHint
                          )
    self.controller = Ui_Controller()
    self.controller.setupUi(self)

    self._graphstore = store

    if rec_uri == 'edf':         ##################
      self._recording = edf.EDFRecording.open('/Users/dave/biosignalml/testdata/swa49.edf')
      self._recording.graph_uri = None
    else:                        ##################
      self._recording = store.get_recording_with_signals(rec_uri)

    annotator = wfdbAnnotation   ##################

    if self._recording is None: raise IOError("Unknown recording: %s" % rec_uri)
    self._start = start
    self._duration = duration

    self.controller.rec_posn = QtGui.QLabel(self)
    self.controller.rec_posn.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
    self.controller.rec_posn.resize(self.controller.rec_start.size())

    self.setWindowTitle(str(self._recording.uri))
##    self.controller.title.setText('')  ##  starttime, duration, .... str(recording.uri))
    self.controller.description.setHtml('<p>'
                                    + '</p><p>'.join([str(a.comment) for a in recording.annotations])
                                    +   '</p>')

    self.model = SignalInfo(self._recording)
    self.controller.signals.setModel(self.model)
    self.controller.signals.setColumnWidth(0, 25)

    self.viewer = ChartForm(start, duration)
    self.viewer.setWindowTitle(str(self._recording.uri))
    self.model.rowVisible.connect(self.viewer.setPlotVisible)
    self.model.rowMoved.connect(self.viewer.movePlot)
    self.controller.signals.rowSelected.connect(self.viewer.plotSelected)

    self._setupSlider()

    interval = self._recording.interval(start, duration)
    for s in self._recording.signals():
      uri = signal_uri(s)
      if str(s.units) == str(uom.UNITS.AnnotationData.uri):
        self.viewer.addEventPlot(uri, s.label, annotator)
      else:
        try: units = uom.RESOURCES[str(s.units)].label
        except: units = str(s.units)
        self.viewer.addSignalPlot(uri, s.label, units) ## , ymin=s.minValue, ymax=s.maxValue)
      for d in s.read(interval): self.viewer.appendPlotData(uri, d)

    # self.setFocusPolicy(QtCore.Qt.StrongFocus) # Needed to handle key events
    self.viewer.showMaximized()
    self.viewer.raise_()

  def showEvent(self, event):
  #--------------------------
#    if self.controller.rec_posn.pos().y() == 0:  # After laying out controller
    self._setSliderTimePosn(self._start)
    QtGui.QWidget.showEvent(self, event)

  def _setSliderTime(self, label, time):
  #-------------------------------------
    ## Show as HH:MM:SS
    label.setText(str(self._sliderrange.map(time)))

  def _setSliderTimePosn(self, time):
  #----------------------------------
    self._setSliderTime(self.controller.rec_posn, time)
    sb = self.controller.segment
    self.controller.rec_posn.move(  ## 44 = approx width of scroll end arrows
      sb.pos().x() + (sb.width()-44)*time/self._recording.duration,
      self.controller.rec_start.pos().y() - 12
      )

  def _setupSlider(self):
  #----------------------
    duration = self._recording.duration
    if duration == 0: return
    self._sliderrange = NumericRange(0.0, duration)
    sb = self.controller.segment
    sb.setMinimum(0)
    scrollwidth = 10000
    sb.setPageStep(scrollwidth*self._duration/duration)
    sb.setMaximum(scrollwidth - sb.pageStep())
    sb.setValue(scrollwidth*self._start/duration)
    self._setSliderTime(self.controller.rec_start, 0.0)
    self._setSliderTime(self.controller.rec_end, duration)

  def _sliderMoved(self):
  #----------------------
    sb = self.controller.segment
    duration = self._recording.duration
    width = sb.maximum() + sb.pageStep() - sb.minimum()
    newstart = sb.value()*duration/float(width)
    self._setSliderTimePosn(newstart)
    if not self.controller.segment.isSliderDown() and newstart != self._start:
      self.viewer.resetPlots()
      interval = self._recording.interval(newstart, self._duration)
      for s in self._recording.signals():
        for d in s.read(interval):
      self.viewer.setTimeRange(newstart, self._duration)
      self._start = newstart
          self.viewer.appendPlotData(signal_uri(s), d)

  def on_segment_valueChanged(self, position):
  #-------------------------------------------
    self._sliderMoved()
    # Sluggish if large data segments with tracking...
  # Tracking is on, show time at slider posiotion
  # But also catch slider released and use this to refresh chart data...

  def on_segment_sliderReleased(self):
  #-----------------------------------
    self._sliderMoved()

  def on_allsignals_toggled(self, state):
  #--------------------------------------
    self.model.setVisibility(state)


  #def keyPressEvent(self, event):   ## Also need to do so in chart...
  #------------------------------    ## And send us hide/show messages or keys



if __name__ == "__main__":
#=========================

  from biosignalml.rdf.sparqlstore import Virtuoso
  from biosignalml.repository import BSMLStore

  logging.basicConfig(format='%(asctime)s: %(message)s')
  logging.getLogger().setLevel('DEBUG')

  ## Replace following with Python arg parser...
  if len(sys.argv) <= 1:
    print "Usage: %s recording_uri [start] [duration]" % sys.argv[0]
    sys.exit(1)

  rec_uri = sys.argv[1]

  if len(sys.argv) >= 3:
    try:
      start = float(sys.argv[2])
    except:
      print "Invalid start time"
      sys.exit(1)
  else:
    start = 0.0

  if len(sys.argv) >= 4:
    try:
      duration = float(sys.argv[3])
    except:
      print "Invalid duration"
      sys.exit(1)
  else:
    duration = 60.0

  app = QtGui.QApplication(sys.argv)

  store = BSMLStore('http://devel.biosignalml.org', Virtuoso('http://localhost:8890'))
  try:
    ctlr = Controller(store, rec_uri, start, duration)
  except IOError, msg:
    print str(msg)
    sys.exit(1)

  ctlr.show()
  ctlr.raise_()
  ctlr.viewer.raise_()

  #viewer1.save_chart_as_png('test.png')   ## Needs to be via 'Save' button/menu and file dialog...

  sys.exit(app.exec_())
