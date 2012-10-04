import sys
import logging

from PyQt4 import QtCore, QtGui

from ui.chart      import Ui_Chart
from ui.controller import Ui_Controller

import biosignalml.formats.hdf5 as hdf5
import biosignalml.formats.edf  as edf
import biosignalml.units.ontology as uom


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

  rowVisible = QtCore.pyqtSignal(str, bool)   # id, state
  rowMoved = QtCore.pyqtSignal(str, str)      # from_id, to_id

  HEADER    = [ '', 'Label', 'Uri' ]
  ID_COLUMN = 2                               # Uri is ID


  def __init__(self, recording, *args, **kwds):
  #--------------------------------------------
    QtCore.QAbstractTableModel.__init__(self, *args, **kwds)
    self._rows = [ [True, s.label, str(s.uri)] for n, s in enumerate(recording.signals()) ]


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

  def __init__(self, recording, start, duration, order=None, annotator=None, parent=None):
  #---------------------------------------------------------------------------------------
    QtGui.QWidget.__init__(self, parent, QtCore.Qt.WindowStaysOnTopHint)
    self.controller = Ui_Controller()
    self.controller.setupUi(self)
    self.setWindowTitle(str(recording.uri))
##    self.controller.title.setText('')  ##  starttime, duration, .... str(recording.uri))
    self.controller.description.setHtml('<p>'
                                    + '</p><p>'.join([str(a.comment) for a in recording.annotations])
                                    +   '</p>')

    self.model = SignalInfo(recording)
    self.controller.signals.setModel(self.model)
    self.controller.signals.setColumnWidth(0, 25)

    self.viewer = ChartForm(start, duration)
    self.viewer.setWindowTitle(str(recording.uri))
    self.model.rowVisible.connect(self.viewer.setPlotVisible)
    self.model.rowMoved.connect(self.viewer.movePlot)
    self.controller.signals.rowSelected.connect(self.viewer.plotSelected)

    segment = recording.interval(start, duration)
    for n, s in enumerate(recording.signals()):
      if str(s.units) == str(uom.UNITS.AnnotationData.uri):
        self.viewer.addEventPlot(s.uri, s.label, annotator)
      else:
        try: units = uom.RESOURCES[str(s.units)].label
        except: units = str(s.units)
        self.viewer.addSignalPlot(s.uri, s.label, units) ## , ymin=s.minValue, ymax=s.maxValue)
      for d in s.read(segment): self.viewer.appendPlotData(s.uri, d)

    self.viewer.showMaximized()
    self.viewer.raise_()


  def on_allsignals_toggled(self, state):
  #--------------------------------------
    self.model.setVisibility(state)


    """
    for n, s in enumerate(recording.signals()):
      if s.rate:                  ###### Need attribute for Signal
        self.viewer.addSignalPlot(n, label, units)
      else:                       ###### or Annotation...
        ## Where does annotation come from ??
        self.viewer.addEventPlot(n, label, wfdbAnnotation)
    """




if __name__ == "__main__":
#=========================

  from biosignalml.rdf.sparqlstore import Virtuoso
  from biosignalml.repository import BSMLStore


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

  if len(sys.argv) <= 1:
    print "Usage: %s recording_uri [start] [duration]" % sys.argv[0]
    sys.exit(1)

  app = QtGui.QApplication(sys.argv)
  store = BSMLStore('http://devel.biosignalml.org', Virtuoso('http://localhost:8890'))
  recording = store.get_recording_with_signals(sys.argv[1])
  if recording is None:
    print "Unknown recording"
    sys.exit(1)

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

  recording.annotations = [ store.get_annotation(ann, recording.graph_uri)
                              for ann in store.annotations(recording.uri, recording.graph_uri) ]

  ctlr = Controller(recording, start, duration, annotator=wfdbAnnotation)

  ctlr.show()
  ctlr.raise_()
  ctlr.viewer.raise_()

  #viewer1.save_chart_as_png('test.png')   ## Needs to be via 'Save' button/menu and file dialog...


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
