#===============================================================================

import sys
import re
import logging
from types import FunctionType

#===============================================================================

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import pyqtSignal, pyqtSlot

#===============================================================================

from biosignalml import BSML
from biosignalml.data import DataSegment
from biosignalml.data.time import Interval
import biosignalml.model
import biosignalml.units as uom
from biosignalml.formats.hdf5 import HDF5Recording

#===============================================================================

from mainwindow        import Ui_MainWindow
from ui.signallist     import Ui_SignalList
from ui.annotationlist import Ui_AnnotationList
from ui.scroller       import Ui_Scroller

from nrange import NumericRange
from table import SortedTable

#===============================================================================

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

#===============================================================================

PREFIXES = {
  'bsml': 'http://www.biosignalml.org/ontologies/2011/04/biosignalml#',
  'dct':  'http://purl.org/dc/terms/',
  'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
  'pbank':	'http://www.biosignalml.org/ontologies/examples/physiobank#',
  }

def abbreviate_uri(uri):
#=======================
  v = str(uri)
  for pfx, ns in PREFIXES.items():
    if v.startswith(ns): return '%s:%s' % (pfx, v[len(ns):])
  return v

def expand_uri(uri):
#===================
  v = str(uri)
  for pfx, ns in PREFIXES.items():
    if v.startswith(pfx+':'): return ns + v[len(pfx)+1:]
  return v

def signal_uri(signal):
#======================
  prefix = str(signal.recording.uri)
  uri = str(signal.uri)
  if uri.startswith(prefix): return uri[len(prefix):]
  else:                      return uri

#===============================================================================

class SignalReadThread(QtCore.QThread):
#======================================

  append_points = pyqtSignal(str, DataSegment)

  def __init__(self, sig, interval, plotter):
  #------------------------------------------
    QtCore.QThread.__init__(self)
    self._signal = sig
    self._id = signal_uri(sig)
    self._interval = interval
    self.append_points.connect(plotter.ui.chart.appendData)

  def run(self):
  #-------------
    self._exit = False
    self.append_points.emit(self._id, DataSegment(0, None))
    try:
      for d in self._signal.read(self._interval, maxpoints=20000):
        self.append_points.emit(self._id, d)
        if self._exit: break
    except Exception as msg:
      raise  ########################################
      logging.error(msg)

  def stop(self):
  #--------------
    self._exit = True

#===============================================================================

class SignalInfo(QtCore.QAbstractTableModel):
#============================================

  rowVisible = pyqtSignal(str, bool)   # id, state
  rowMoved = pyqtSignal(str, str)      # from_id, to_id

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
    if orientation == QtCore.Qt.Orientation.Horizontal:
      if role == QtCore.Qt.ItemDataRole.DisplayRole:
        return self.HEADER[section]
      elif role == QtCore.Qt.ItemDataRole.TextAlignmentRole:
        return QtCore.Qt.AlignmentFlag.AlignLeft
      elif role == QtCore.Qt.ItemDataRole.FontRole:
        font = QtGui.QFont(QtWidgets.QApplication.font())
        font.setBold(True)
        return font

  def data(self, index, role):
  #---------------------------
    if   role == QtCore.Qt.ItemDataRole.DisplayRole:
      if index.column() != 0:
        return str(self._rows[index.row()][index.column()])
      else:
        return QtCore.QVariant()
    elif role == QtCore.Qt.ItemDataRole.CheckStateRole:
      if index.column() == 0:
        return QtCore.Qt.CheckState.Checked if self._rows[index.row()][0] else QtCore.Qt.CheckState.Unchecked

  def setData(self, index, value, role):
  #-------------------------------------
    if role == QtCore.Qt.ItemDataRole.CheckStateRole and index.column() == 0:
      self._rows[index.row()][0] = (value == QtCore.Qt.CheckState.Checked)
      self.rowVisible.emit(self._rows[index.row()][self.ID_COLUMN], (value == QtCore.Qt.CheckState.Checked))
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
      return QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsUserCheckable | QtCore.Qt.ItemFlag.ItemIsSelectable
    else:
      return QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable

  def setVisibility(self, visible):
  #--------------------------------
    for r in range(len(self._rows)):
      self.setData(self.createIndex(r, 0),
                   QtCore.Qt.CheckState.Checked if visible else QtCore.Qt.CheckState.Unchecked,
                   QtCore.Qt.ItemDataRole.CheckStateRole)

#===============================================================================

class AnnotationTable(object):
#=============================

  @staticmethod
  def header():
  #------------
    return ['', 'Start', 'End', 'Duration',  'Type', 'Annotation', 'Tags']


  '''
  Is this the place to actually hold the table?

  And have a 'get_cell(row, col)' that returns QVariant?

  '''

  @staticmethod
  def row(uri, times, type, text, tagtext=''):
  #-------------------------------------------
    return [str(uri)] + times + [ type, text, tagtext ]

#===============================================================================

class SignalList(QtWidgets.QWidget):
#===================================

  add_event_plot = pyqtSignal(str, str, FunctionType) ## , bool, DataSegment)
  add_signal_plot = pyqtSignal(str, str, str) ## , bool, DataSegment, float, float)
  show_signals = pyqtSignal(Interval)

  def __init__(self, recording, annotator, parent=None):
  #-----------------------------------------------------
    QtWidgets.QWidget.__init__(self, parent)
    self.ui = Ui_SignalList()
    self.ui.setupUi(self)
    self._recording = recording
    self._annotator = annotator
    self.model = SignalInfo(recording)
    self.ui.signals.setModel(self.model)
    self.ui.signals.setColumnWidth(0, 25)

  def plot_signals(self, start, duration):
  #---------------------------------------
    interval = self._recording.interval(start, duration)
    for s in self._recording.signals():
      uri = signal_uri(s)
      if str(s.units) == str(uom.UNITS.AnnotationData.uri):
        self.add_event_plot.emit(uri, s.label, self._annotator)
      else:
        try:
          units = uom.RESOURCES[str(s.units)].label
        except:
          u = str(s.units)
          units = u[u.find('#')+1:]
        self.add_signal_plot.emit(uri, s.label,
                                  units.replace('_per_', '/')
                                       .replace('micro', 'µ')
                                       .replace('milli', 'm')
                                       .replace('volt', 'V')
                                       .replace('cm2', 'cm²')
                                       )
                                  ## , ymin=s.minValue, ymax=s.maxValue)
    self.show_signals.emit(interval)

  def on_allsignals_toggled(self, state):
  #--------------------------------------
    self.model.setVisibility(state)

#===============================================================================

class AnnotationList(QtWidgets.QWidget):
#=======================================

  add_annotation = pyqtSignal(str, float, float, str, list, bool)
  delete_annotation = pyqtSignal(str)
  move_plot = pyqtSignal(float)
  set_marker = pyqtSignal(float)
  set_slider_value = pyqtSignal(float)
  show_slider_time = pyqtSignal(float)

  def __init__(self, recording, semantic_tags, parent=None):
  #---------------------------------------------------------

    QtWidgets.QWidget.__init__(self, parent)
    self.ui = Ui_AnnotationList()
    self.ui.setupUi(self)

    self._recording = recording
    self._semantic_tags = semantic_tags
    self._make_uri = self._recording.uri.make_uri    # Method for minting new URIs
    self._timerange = NumericRange(0.0, recording.duration)  ### ???????
    self._annotations = [ ]     # tuple(uri, start, end, text, tags, editable, resource)
    for ann in self._recording.graph.get_annotations():
      if ann.time is None:
        annstart = None
        annend   = None
      else:
        annstart = ann.time.start
        annend   = None if ann.time.duration in [None, 0.0] else ann.time.end
      tags = ann.tags
      if not isinstance(tags, list): tags = [ tags ]
      self._annotations.append( (ann.uri, annstart, annend,
                                 ann.comment if ann.comment is not None else '',
                                 tags, True, ann) )
    self._annotation_table = SortedTable(self.ui.annotations,
                                         AnnotationTable.header(),
                                         [AnnotationTable.row(ann[0],
                                                              self._make_ann_times(ann[1], ann[2]),
                                                              'Annotation' if ann[5] else 'Event',
                                                              ann[3],
                                                              self._tag_labels(ann[4]))
                                            for ann in self._annotations],
                                         parent=self)

#    for e in [self._recording.graph.get_event(evt)
#                for evt in self._recording.graph.get_event_uris(timetype=BSML.Interval)]:
#      if e.time.end is None: e.time.end = e.time.start
#      self._annotations.append( (str(e.uri), e.time.start, e.time.end, abbreviate_uri(e.eventtype), [], False, e) )

    self._events = { }
    self._event_type = None
    self._event_rows = None
    self.ui.events.addItem('None')
    self.ui.events.insertItems(1, ['%s (%s)' % (abbreviate_uri(etype), count)
      for etype, count in self._recording.graph.get_event_types(counts=True)])
      # if no duration ...
    self.ui.events.addItem('All')
    self._event_type = 'None'

  @pyqtSlot()
  def show_annotations(self):
  #--------------------------
    for a in self._annotations:  # tuple(uri, start, end, text, tags, editable, resource)
      if a[1] is not None: self.add_annotation.emit(*a[:6])

  def _make_ann_times(self, start, end):
  #-------------------------------------
    if start is None:
      return ['', '', '']
    else:
      nstart = self._timerange.map(start)  # Normalise for display
      if end is not None:
        nend = self._timerange.map(end)
        return [ nstart, nend, nend - nstart ]
      else:
        return [ nstart, '', '' ]

  def _tag_labels(self, tags):
  #---------------------------
    if tags is None:
      return ''
    else:
      return ', '.join(sorted([self._semantic_tags.get(str(t), str(t)) for t in tags]))

  def _find_annotation(self, id):
  #------------------------------
    for ann in self._annotations:
      if id == ann[0]: return ann

  def _delete_annotation(self, id):
  #--------------------------------
    for n, ann in enumerate(self._annotations):
      if id == ann[0]:
        del self._annotations[n]
        return

  def disabled_on_annotations_doubleClicked(self, index):   ####
  #---------------------------------------------
    source = index.model().mapToSource(index)
    id = source.model().createIndex(source.row(), 0).data()
    ann = self._find_annotation(id)
    time = None
    duration = None
    if ann and ann[1] is not None:
      time = ann[1]
      if ann[2] is not None:
        duration = ann[2] - time
    else:
      evt = self._events.get(id, None)
      if evt is not None:
        time = evt[0]
        duration = evt[1]
    if time is not None:
      if duration is not None:
        start = max(0.0, time - duration/2.0)
        end = min(time + duration + duration/2.0, self._recording.duration)
        self._duration = end - start
      else:
        start = max(0.0, time - self._duration/4.0)
      self.move_plot.emit(start)
      self.set_slider_value.emit(start)
      self.show_slider_time.emit(start)
      self.set_marker.emit(time)

  def on_events_currentIndexChanged(self, index):
  #----------------------------------------------
    if (self._event_type is None      # Setting up
     or not isinstance(index, str)): return
    if self._event_rows is not None:
      self._annotation_table.removeRows(self._event_rows)
    if index == 'None':
      self._event_rows = None
      return
    if index == 'All': etype = None
    else: etype = expand_uri(str(index).rsplit(' (', 1)[0])
    events = [ self._recording.graph.get_event(evt)
                 for evt in self._recording.graph.get_event_uris(eventtype=etype, timetype=BSML.Instant) ]
    self._events = { str(event.uri): (event.time.start, event.time.duration) for event in events }
    self._event_rows = self._annotation_table.appendRows([ AnnotationTable.row(event.uri,
                                                            [self._timerange.map(event.time.start),
                                                             self._timerange.map(event.time.end),
                                                             event.time.duration], 'Event',
                                                            abbreviate_uri(event.eventtype))
                                                         for event in events ])
##    self._adjust_layout()

  @pyqtSlot(float, float, str, list, str)
  def annotationAdded(self, start, end, text, tags, predecessor=None):
  #-------------------------------------------------------------------
    if text or tags:
      segment = biosignalml.model.Segment(self._make_uri(),
                                          self._recording,
                                          self._recording.interval(start, end=end))
      self._recording.add_resource(segment)
      self._add_annotation(segment, text, tags, predecessor)
      self._recording._modified = True

  def _add_annotation(self, about, text, tags, predecessor=None):
  #--------------------------------------------------------------
    annotation = biosignalml.model.Annotation(self._make_uri(),
                                              about=about,
                                              comment=text, tags=tags,
                                              precededBy=predecessor)
    self._recording.add_resource(annotation)
    if annotation.time is not None:
      (start, end) = (annotation.time.start, annotation.time.end)
    else:
      (start, end) = (None, None)
    self._annotation_table.appendRows([ AnnotationTable.row(annotation.uri,
                                                            self._make_ann_times(start, end),
                                                            'Annotation', text,
                                                            self._tag_labels(tags)) ])
    self._annotations.append((str(annotation.uri), start, end, text, tags, True, annotation))
    self.add_annotation.emit(annotation.uri, start, end, text, tags, True)

  def _remove_annotation(self, id):
  #--------------------------------
    self._annotation_table.deleteRow(id)
    self._delete_annotation(id)
    self.delete_annotation.emit(id)

  @pyqtSlot(str, str, list)
  def annotationModified(self, id, text, tags):
  #--------------------------------------------
    ann = self._find_annotation(id)
    if ann is not None:
      self._remove_annotation(id)
      if text or tags:
        self._add_annotation(ann[6].about, text, tags, predecessor=id)
      self._recording._modified = True

  @pyqtSlot(str)
  def annotationDeleted(self, id):
  #-------------------------------
    self._remove_annotation(id)
    self._recording.remove_resource(id)
    self._recording._modified = True


class Scroller(QtWidgets.QWidget):
#=================================

  set_plot_time_range = pyqtSignal(float, float)
  show_signals = pyqtSignal(Interval)
  show_annotations = pyqtSignal()

  def __init__(self, recording, start, duration, parent=None):
  #-----------------------------------------------------------
    QtWidgets.QWidget.__init__(self, parent)
    self.ui = Ui_Scroller()
    self.ui.setupUi(self)
    self.ui.rec_posn = QtWidgets.QLabel(self)
    self.ui.rec_posn.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)
    self.ui.rec_posn.resize(self.ui.rec_start.size())
    self._timerange = NumericRange(0.0, duration)
    self._recording = recording
    self._start = start
    self._duration = duration       ### v's recording's duration ???

  def _set_slider_time(self, label, time):
  #---------------------------------------
    ## Show as HH:MM:SS
    label.setText(str(self._timerange.map(time, -1)))

  @pyqtSlot(float)
  def show_slider_time(self, time):
  #--------------------------------
    self._set_slider_time(self.ui.rec_posn, time)
    sb = self.ui.segment
    self.ui.rec_posn.move(  ## 50 = approx width of scroll end arrows
      20 + sb.pos().x() + (sb.width()-50)*time/self._duration,
      self.ui.rec_start.pos().y() + 6)

  @pyqtSlot(float)
  def set_slider_value(self, time):
  #---------------------------------
    sb = self.ui.segment
    width = sb.maximum() + sb.pageStep() - sb.minimum()
    sb.setValue(width*time/self._duration)

  def setup_slider(self):
  #----------------------
    self._sliding = True            ## So we don't move_plot() when sliderMoved()
    self._move_timer = None         ## is triggered by setting the slider's value
    duration = self._recording.duration     ## Versus slider's duration
    if duration == 0: return
    sb = self.ui.segment
    sb.setMinimum(0)
    scrollwidth: int = 10000
    sb.setPageStep(int(scrollwidth*self._duration/duration))
    sb.setMaximum(scrollwidth - sb.pageStep())
    sb.setValue(int(scrollwidth*self._start/duration))
    self._set_slider_time(self.ui.rec_start, 0.0)
    self._set_slider_time(self.ui.rec_end, duration)

  def _stop_move_timer(self):
  #--------------------------
    if self._move_timer is not None:
      self.killTimer(self._move_timer)
      self._move_timer = None

  def _start_move_timer(self):
  #---------------------------
    if self._move_timer is not None:
      self.killTimer(self._move_timer)
    self._move_timer = self.startTimer(100)  # 100ms

  def timerEvent(self, event):
  #---------------------------
    if self._move_timer is not None:
      self._stop_move_timer()
      self.move_plot(self._newstart)

  def _slider_moved(self):
  #-----------------------
    sb = self.ui.segment
    duration = self._recording.duration
    width = sb.maximum() + sb.pageStep() - sb.minimum()
    self._newstart = sb.value()*duration/float(width)
    self.show_slider_time(self._newstart)
    if self.ui.segment.isSliderDown():
      self._start_move_timer()
      self._sliding = True
    elif self._sliding:
      if self._move_timer is not None:
        self._stop_move_timer()
        self.move_plot(self._newstart)
      self._sliding = False
    else:
      self.move_plot(self._newstart)

  @pyqtSlot(float)
  def move_plot(self, start):
  #---------------------------
    if start != self._start:
      self.show_signals.emit(self._recording.interval(start, self._duration))
      self.set_plot_time_range.emit(start, self._duration)
      self._start = start
      self.show_annotations.emit()

  def on_segment_valueChanged(self, position):
  #-------------------------------------------
    self._slider_moved()
    # Sluggish if large data segments with tracking...
  # Tracking is on, show time at slider position
  # But also catch slider released and use this to refresh chart data...

  def on_segment_sliderReleased(self):
  #-----------------------------------
    self._slider_moved()

#===============================================================================

class MainWindow(QtWidgets.QMainWindow):
#=======================================

  reset_annotations = pyqtSignal()
##  resize_annotation_list = pyqtSignal()
##  show_slider_time = pyqtSignal(float)


  def __init__(self, recording, start=0.0, end=None, semantic_tags={ }, annotator=None):
  #-------------------------------------------------------------------------------------

    QtWidgets.QMainWindow.__init__(self)

    if end is None:
      duration = recording.duration
      if duration is None or duration <= 0.0:
        recording.duration = duration = 60.0    ######
    elif start <= end:
      duration = end - start
    else:
      duration = start - end
      start = end
    self._readers = [ ]
    self._recording = recording
    self._recording._modified = False
    self._start = start        ## Used in adjust_layout

    signals = SignalList(recording, annotator, self)
    annotations = AnnotationList(recording, semantic_tags, self)
    scroller = Scroller(recording, start, duration, self)

    self.ui = Ui_MainWindow()
    self.ui.setupUi(self, signals, annotations, scroller)
    self.setWindowTitle(recording.uri)

    # Setup chart
    self.ui.chartform.setTimeRange(start, duration)
    chart = self.ui.chartform.ui.chart
    chart.setId(uri)
    chart.setSemanticTags(semantic_tags)
    chart.exportRecording.connect(self.exportRecording)

    # Connections with signal list
    signals.add_event_plot.connect(chart.addEventPlot)
    signals.add_signal_plot.connect(chart.addSignalPlot)
    signals.show_signals.connect(self.plot_signals)
    signals.model.rowVisible.connect(chart.setPlotVisible)
    signals.model.rowMoved.connect(chart.movePlot)
    signals.ui.signals.rowSelected.connect(chart.plotSelected)

    # Connections with annotation list
    annotations.add_annotation.connect(chart.addAnnotation)
    annotations.delete_annotation.connect(chart.deleteAnnotation)
    annotations.set_marker.connect(chart.setMarker)
    annotations.move_plot.connect(scroller.move_plot)
    annotations.set_slider_value.connect(scroller.set_slider_value)
    annotations.show_slider_time.connect(scroller.show_slider_time)
    chart.annotationAdded.connect(annotations.annotationAdded)
    chart.annotationModified.connect(annotations.annotationModified)
    chart.annotationDeleted.connect(annotations.annotationDeleted)

    # Connections with scroller
    scroller.set_plot_time_range.connect(chart.setTimeRange)
    scroller.show_signals.connect(self.plot_signals)
    scroller.show_annotations.connect(annotations.show_annotations)

    # Connect our signals
    self.reset_annotations.connect(chart.resetAnnotations)
##    self.resize_annotation_list.connect(annotations.annotations.resizeCells)
##    self.show_slider_time.connect(scroller.show_slider_time)

    # Everything connected, let's go...
    signals.plot_signals(start, duration)
    annotations.show_annotations()
    scroller.setup_slider()

#    self.ui.chartform._user_zoom_index = self.ui.timezoom.count()
#    self.ui.chartform.ui.chart.zoomChart.connect(self.zoom_chart)

    ## self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus) # Needed to handle key events

  def __del__(self):
  #-----------------
    self._stop_readers()

  @pyqtSlot(Interval)
  def plot_signals(self, interval):
  #---------------------------------
    self._stop_readers()
    self.reset_annotations.emit()
    for s in self._recording.signals():   ## Why not only ones currently selected ????
      self._readers.append(SignalReadThread(s, interval, self.ui.chartform))
      self._readers[-1].start()

  def _stop_readers(self):
  #-----------------------
    for t in self._readers: t.stop()
    while True:
      stopped = True
      for t in self._readers:
        stopped = stopped and t.wait(10)
      if stopped: break
    self._readers = [ ]

  '''   ### Now happens in appropriate widgets
  @pyqtSlot()
  def adjust_layout(self):
  #------------------------
    self.resize_annotation_list.emit()
    self.show_slider_time.emit(self._start)

  def resizeEvent(self, event):
  #----------------------------
    self.adjust_layout()

  def showEvent(self, event):
  #--------------------------
#    if self.controller.rec_posn.pos().y() == 0:  # After laying out controller
    self.adjust_layout()
    QtWidgets.QWidget.showEvent(self, event)
  '''

  def exportRecording(self, start, end):
  #-------------------------------------
    ## This is where we create a BSML file with current set of displayed signals
    ## along with events and annotations starting or ending in the interval, and
    ## provenance linking back to the original.
    print('export', start, end)


  #def keyPressEvent(self, event):   ## Also need to do so in chart...
  #------------------------------    ## And send us hide/show messages or keys
  #  pass

  def closeEvent(self, event):
  #---------------------------
    if self._recording._modified:
      self._recording._modified = False
      self._recording.close()

#===============================================================================

if __name__ == "__main__":
#=========================

  import biosignalml.client

  logging.basicConfig(format='%(asctime)s %(levelname)8s %(threadName)s: %(message)s')
#  logging.getLogger().setLevel('DEBUG')

  ## Replace following with Python arg parser...
  if len(sys.argv) <= 1:
    print("Usage: %s RECORDING [start] [duration]" % sys.argv[0])
    sys.exit(1)
  uri = sys.argv[1]
  if len(sys.argv) >= 3:
    try:
      start = float(sys.argv[2])
    except:
      print("Invalid start time")
      sys.exit(1)
  else:
    start = 0.0
  if len(sys.argv) >= 4:
    try:
      end = start + float(sys.argv[3])
    except:
      print("Invalid duration")
      sys.exit(1)
  else:
    end = None

  app = QtWidgets.QApplication(sys.argv)
  app.setStyle("fusion")   ## For Ubuntu 14.04
  try:
    if uri.startswith('http://'):
      store = biosignalml.client.Repository(uri)
      recording = store.get_recording(uri)
      semantic_tags = store.get_semantic_tags()
    else:
      recording = HDF5Recording.open(uri)
      semantic_tags = { 'http://standards/org/ontology#tag1': 'Tag 1',   ### Load from file
                        'http://standards/org/ontology#tag2': 'Tag 2',
                        'http://standards/org/ontology#tag3': 'Tag 3',
                        'http://standards/org/ontology#tag4': 'Tag 4',
                      }
    viewer = MainWindow(recording, start, end, semantic_tags=semantic_tags, annotator=wfdbAnnotation)
    viewer.show()
  except IOError as msg:
    sys.exit(str(msg))
  except:
    raise  ###################
  sys.exit(app.exec_())

#===============================================================================

