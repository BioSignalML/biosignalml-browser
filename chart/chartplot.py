import math
import logging
import collections
import numpy as np
from types import FunctionType

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import QtOpenGL
from PyQt5.QtCore import pyqtSignal, pyqtSlot

from biosignalml.data import DataSegment

from nrange import NumericRange
from annotation import AnnotationDialog

##ChartWidget = QtWidgets.QWidget   # Hangs if > 64K points
ChartWidget = QtOpenGL.QGLWidget    # Faster, anti-aliasing not quite as good QWidget


try:
## Borrowed from http://home.gna.org/veusz/
  from veusz.qtloops import addNumpyToPolygonF

  def make_polygon(points):
  #------------------------
    poly = QtGui.QPolygonF()
    addNumpyToPolygonF(poly, points[..., 0], points[..., 1])
    return poly

except ImportError:

  def make_polygon(points):
  #------------------------
    return QtGui.QPolygonF([QtCore.QPointF(pt[0], pt[1]) for pt in points])


# Margins of plotting region within chart, in pixels
MARGIN_LEFT   =  120
MARGIN_RIGHT  =  80
MARGIN_TOP    = 100
MARGIN_BOTTOM =  40


traceColour      = QtGui.QColor('green')
selectedColour   = QtGui.QColor('red')             ## When signal is selected in controller
textColour       = QtGui.QColor('darkBlue')
markerColour     = QtGui.QColor('blue')
marker2Colour    = QtGui.QColor(0xCC, 0x55, 0x00)  ## 'burnt orange'
gridMinorColour  = QtGui.QColor(128, 128, 255, 63)
gridMajorColour  = QtGui.QColor(0,     0, 128, 63)
selectionColour  = QtGui.QColor(220, 255, 255)     ## Of selected region
selectEdgeColour = QtGui.QColor('cyan')
selectTimeColour = QtGui.QColor('black')
selectLenColour  = QtGui.QColor('darkRed')

ANN_START        = 20                              ## Pixels from top to first bar
ANN_LINE_WIDTH   = 8
ANN_LINE_GAP     = 2
ANN_COLOURS      = [ QtGui.QColor('red'),     QtGui.QColor('blue'),     QtGui.QColor('magenta'),
                     QtGui.QColor('darkRed'), QtGui.QColor('darkBlue'), QtGui.QColor('cyan') ]

alignLeft        = 0x01
alignRight       = 0x02
alignCentre      = 0x03
alignTop         = 0x04
alignBottom      = 0x08
alignMiddle      = 0x0C
alignCentred     = 0x0F


def drawtext(painter, x, y, text, mapX=True, mapY=True, align=alignCentred, fontSize=None, fontWeight=None):
#-----------------------------------------------------------------------------------------------------------
  if not text: return
  lines = text.split('\n')
  xfm = painter.transform()
  if mapX or mapY:
    pt = xfm.map(QtCore.QPointF(x, y))  # Assume affine mapping
    if mapX: x = pt.x()
    if mapY: y = pt.y()
  painter.resetTransform()
  font = painter.font()
  if fontSize is not None or fontWeight is not None:
    newfont = QtGui.QFont(font)
    if fontSize: newfont.setPointSize(fontSize)
    if fontWeight: newfont.setWeight(fontWeight)
    painter.setFont(newfont)
  metrics = painter.fontMetrics()
  th = (metrics.xHeight() + metrics.ascent())/2.0  # Compromise...
  adjust = (len(lines)-1)*metrics.height()  ## lineSpacing()
  if   (align & alignMiddle) == alignMiddle: ty = y + (th-adjust)/2.0
  elif (align & alignTop)    == alignTop:    ty = y + th
  else:                                      ty = y - adjust
  for t in lines:
    tw = metrics.width(t)
    if   (align & alignCentre) == alignCentre: tx = x - tw/2.0
    elif (align & alignRight)  == alignRight:  tx = x - tw
    else:                                      tx = x
    painter.drawText(QtCore.QPointF(tx, ty), t)
    ty += metrics.height()                  ## lineSpacing()
  painter.setFont(font)             # Reset, in case changed above
  painter.setTransform(xfm)


class SignalPlot(object):
#========================
  """
  A single trace.
  """

  def __init__(self, label, units, data=None, ymin=None, ymax=None):
  #-----------------------------------------------------------------
    self.label = '%s\n(%s)' % (label, units) if units else label
    self.selected = False
    self.reset(ymin, ymax)
    if data: self.appendData(data, ymin, ymax)
    else:    self._setYrange()

  def reset(self, ymin=None, ymax=None):
  #-------------------------------------
    self._ymin = ymin
    self._ymax = ymax
    self._poly = QtGui.QPolygonF()
    self._path = QtGui.QPainterPath()

  def _setYrange(self):
  #--------------------
    if self._ymin == self._ymax:
      if self._ymin: (ymin, ymax) = (self._ymin-abs(self._ymin)/2.0, self._ymax+abs(self._ymax)/2.0)
      else:          (ymin, ymax) = (-0.5, 0.5)
    else:
      (ymin, ymax) = (self._ymin, self._ymax)
    self._range = NumericRange(ymin, ymax)
    self.gridstep = self._range.major
    self.ymin = self._range.start
    self.ymax = self._range.end

  @property
  def gridheight(self):
  #--------------------
    return self._range.major_size

  def appendData(self, data, ymin=None, ymax=None):
  #------------------------------------------------
    if len(data) == 0:
      self.reset(ymin, ymax)
      return
    if ymin is None: ymin = np.amin(data.data)
    if ymax is None: ymax = np.amax(data.data)
    if self._ymin == None or self._ymin > ymin: self._ymin = ymin
    if self._ymax == None or self._ymax < ymax: self._ymax = ymax
    self._setYrange()
    poly = make_polygon(data.points)
    path = QtGui.QPainterPath()
    path.addPolygon(poly)
    self._path.connectPath(path)
    self._poly += poly

  def yValue(self, time):
  #----------------------
    """
    Find the y-value corresponding to a time.
    """
    i = self._index(time)
    if i is not None:
      if i >= (self._poly.size() - 1):
        i = self._poly.size() - 2
      p0 = self._poly.at(i)
      p1 = self._poly.at(i+1)
      if p0.x() == p1.x(): return (p0.y() + p1.y())/2.0
      return p0.y() + (time - p0.x())*(p1.y() - p0.y())/(p1.x() - p0.x())

  def _index(self, time):
  #----------------------
    i = 0
    j = self._poly.size()
    if (time < self._poly.at(0).x()
     or time > self._poly.at(j-1).x()): return None
    while i < j:
      m = (i + j)//2
      if self._poly.at(m).x() <= time: i = m + 1
      else:                            j = m
    return i - 1

  def yPosition(self, timepos):
  #----------------------------
    return None

  def drawTrace(self, painter, start, end, endlabels=False, labelfreq=1, markers=None):
  #------------------------------------------------------------------------------------
    """
    Draw the trace.

    :param painter: The QPainter to use for drawing.
    :param start: The leftmost position on the X-axis.
    :param end: The rightmost position on the X-axis.

    The painter has been scaled so that (0.0, 1.0) is the
    vertical plotting height.
    """
    if self._path is None: return
    painter.scale(1.0, 1.0/(self.ymax - self.ymin))
    painter.translate(0.0, -self.ymin)
    # draw and label y-gridlines.
    n = 0
    y = self.ymin
    while y <= self.ymax:
      painter.setPen(QtGui.QPen(gridMinorColour, 0))
      painter.drawLine(QtCore.QPointF(start, y), QtCore.QPointF(end, y))
      if (labelfreq > 0
       and (endlabels or self.ymin < y < self.ymax)
       and (self.gridheight/labelfreq) > 1 and (n % labelfreq) == 0):
        painter.drawLine(QtCore.QPointF(start-0.005*(end-start), y), QtCore.QPointF(start, y))
        painter.setPen(QtGui.QPen(textColour, 0))
        drawtext(painter, MARGIN_LEFT-20, y, str(y), mapX=False)    # Label grid
      y += self._range.major
      if -1e-10 < y < 1e-10: y = 0.0  #####
      n += 1
    painter.setClipping(True)
    painter.setPen(QtGui.QPen(traceColour if not self.selected else selectedColour, 0))
    # Could find start/end indices and only draw segment
    # rather than rely on clipping...
    painter.drawPath(self._path)
    #painter.drawPolyline(QtGui.QPolygonF(self._points))
    # But very fast as is, esp. when using OpenGL
    painter.setClipping(False)
    if markers:
      xfm = painter.transform()
      for n, t in enumerate(markers):
         painter.setPen(QtGui.QPen(markerColour if n == 0 else marker2Colour, 0))
         y = self.yValue(t)
         if y is not None:
           y = self._range.map(y, extra=1)
           xy = xfm.map(QtCore.QPointF(t, y))
           drawtext(painter, xy.x()+5, xy.y(), str(y), mapX=False, mapY=False, align=alignLeft)


class EventPlot(object):
#=======================
  """
  A single event trace.
  """
  def __init__(self, label, mapping=lambda x: (str(x), str(x)), data=None):
  #------------------------------------------------------------------------
    self.label = label
    self.selected = False
    self._mapping = mapping
    self.reset()
    self.gridheight = 2   ###
    if data: self.appendData(data)

  def reset(self):
  #---------------
    self._events = [ ]
    self._eventpos = []

  def yPosition(self, timepos):
  #----------------------------
    timepos = int(timepos+0.5) + 3                          ## "close to"
    i = 0
    j = len(self._eventpos)
    if j == 0 or timepos < self._eventpos[0][0]: return None
    while i < j:
      m = (i + j)//2
      if self._eventpos[m][0] <= timepos: i = m + 1
      else:                               j = m
    timepos -= 3
    if (timepos-3) <= self._eventpos[i-1][0] < (timepos+3): ## "close to"
      return self._eventpos[i-1][2]

  def appendData(self, data):
  #--------------------------
    if len(data) == 0:
      self.reset()
    else:
      self._events.extend([ (pt[0], self._mapping(pt[1])) for pt in data.points ])

  def drawTrace(self, painter, start, end, markers=None, **kwds):
  #--------------------------------------------------------------
    if not self._events: return
    painter.setClipping(True)
    self._eventpos = []
    for t, event in self._events:
      if event[0]:
        painter.setPen(QtGui.QPen(traceColour if not self.selected else selectedColour, 0))
        painter.drawLine(QtCore.QPointF(t, 0.0), QtCore.QPointF(t, 1.0))
        painter.setPen(QtGui.QPen(textColour, 0))
        drawtext(painter, t, 0.5, event[0])
        xy = painter.transform().map(QtCore.QPointF(t, 0.5))
        self._eventpos.append( (int(xy.x()+0.5), int(xy.y()+0.5), '\n'.join(event[1].split())) )
    painter.setClipping(False)


class ChartPlot(ChartWidget):
#============================
  """
  A Chart is made up of several Plots stacked vertically
  and all sharing the same X-axis (time axis).

  """
  chartPosition = pyqtSignal(int, int, int)
  updateTimeScroll = pyqtSignal(bool)
  annotationAdded = pyqtSignal(float, float, str, list)
  annotationModified = pyqtSignal(str, str, list)
  annotationDeleted = pyqtSignal(str)
  exportRecording = pyqtSignal(str, float, float)
  zoomChart = pyqtSignal(float)

  def __init__(self, parent=None):
  #-------------------------------
    if ChartWidget == QtOpenGL.QGLWidget:
      QtOpenGL.QGLWidget.__init__(self,
        QtOpenGL.QGLFormat(QtOpenGL.QGL.SampleBuffers),
        parent)
    else:
      QtWidgets.QWidget.__init__(self, parent)
    self.setPalette(QtGui.QPalette(QtGui.QColor('black'), QtGui.QColor('white')))
    self.setMouseTracking(True)
    self._id = None
    self._plots = {}        # id --> index in plotlist
    self._plotlist = []     # [id, visible, plot] triples as a list
    self._timezoom = 1.0
    self._markers = [ ]     # List of [xpos, time] pairs
    self._marker = -1       # Index of marker being dragged
    self._selectstart = None
    self._selectend = None
    self._selecting = False
    self._selectmove = None
    self._mousebutton = None
    self._annotations = collections.OrderedDict()  # id --> to tuple(start, end, text, tags, editable)
    self._annrects = []    # List of tuple(rect, id)
    self.semantic_tags = { }

  def setId(self, id):
  #-------------------
    self._id = str(id)

  def setSemanticTags(self, tag_dict):
  #-----------------------------------
    self.semantic_tags = tag_dict    ## { uri: label }

  @pyqtSlot(str, str, str) ## , bool, DataSegment, float, float)
  def addSignalPlot(self, id, label, units, visible=True, data=None, ymin=None, ymax=None):
  #----------------------------------------------------------------------------------------
    plot = SignalPlot(label, units, data, ymin, ymax)
    self._plots[str(id)] = len(self._plotlist)
    self._plotlist.append([str(id), visible, plot])
    self.update()

  @pyqtSlot(str, str, FunctionType) ## , bool, DataSegment)
  def addEventPlot(self, id, label, mapping=lambda x: str(x), visible=True, data=None):
  #------------------------------------------------------------------------------------
    plot = EventPlot(label, mapping, data)
    self._plots[str(id)] = len(self._plotlist)
    self._plotlist.append([str(id), visible, plot])
    self.update()

  @pyqtSlot(str, DataSegment)
  def appendData(self, id, data):
  #------------------------------
    n = self._plots.get(str(id), -1)
    if n >= 0:
      self._plotlist[n][2].appendData(data)
      self.update()

  @pyqtSlot(str, bool)
  def setPlotVisible(self, id, visible=True):
  #------------------------------------------
    n = self._plots.get(str(id), -1)
    if n >= 0:
      self._plotlist[n][1] = visible
      self.update()

  @pyqtSlot(result=list)
  def plotOrder(self):
  #-------------------
    """ Get list of plot ids in display order. """
    return [ p[0] for p in self._plotlist ]

  @pyqtSlot(list)
  def orderPlots(self, ids):
  #-------------------------
    """
    Reorder display to match id list.

    The display position of plots is changed to match the order
    of ids in the list. Plots with ids not in the list are not
    moved. Unknown ids are ignored.
    """
    order = []
    plots = []
    for id in ids:
      n = self._plots.get(str(id), -1)
      if n >= 0:
        order.append(n)
        plots.append(self._plotlist[n])
    for i, n in enumerate(sorted(order)):
      self._plotlist[n] = plots[i]
      self._plots[plots[i][0]] = n
    self.update()

  @pyqtSlot(str, str)
  def movePlot(self, from_id, to_id):
  #----------------------------------
    """ Move a plot, shifting others up or down."""
    n = self._plots.get(str(from_id), -1)
    m = self._plots.get(str(to_id), -1)
    if n >= 0 and m >= 0 and n != m:
      p = self._plotlist[n]
      if n > m:   # shift up
        self._plotlist[m+1:n+1] = self._plotlist[m:n]
        for i in xrange(m+1, n+1): self._plots[self._plotlist[i][0]] = i
      else:       # shift down
        self._plotlist[n:m] = self._plotlist[n+1:m+1]
        for i in xrange(n, m): self._plots[self._plotlist[i][0]] = i
      self._plotlist[m] = p
      self._plots[str(from_id)] = m
    self.update()

  @pyqtSlot(int)
  def plotSelected(self, row):
  #---------------------------
    for n, p in enumerate(self._plotlist):
      p[2].selected = (n == row)
    self.update()

  @pyqtSlot()
  def resetAnnotations(self):
  #--------------------------
    self._annotations = collections.OrderedDict()
    self._annrects = []

  @pyqtSlot(str, float, float, str, dict, bool)
  def addAnnotation(self, id, start, end, text, tags, edit=False):
  #---------------------------------------------------------------
    if end is None: end = start
    if end > self.start and start < self.end:
      self._annotations[str(id)] = (start, end, text, tags, edit)

  @pyqtSlot(str)
  def deleteAnnotation(self, id):
  #------------------------------
    self._annotations.pop(str(id), None)
    self.update()

  def resizeEvent(self, e):
  #-----------------------
    self.chartPosition.emit(self.pos().x() + MARGIN_LEFT,
                            self.width() - (MARGIN_LEFT + MARGIN_RIGHT),
                            self.pos().y() + self.height())
  
  def paintEvent(self, e):
  #-----------------------
    self._draw(self)

  def _draw(self, device):
  #-----------------------
    qp = QtGui.QPainter()
    qp.begin(device)

    qp.setRenderHint(QtGui.QPainter.Antialiasing)

    w = device.width()
    h = device.height()
    self._plot_width  = w - (MARGIN_LEFT + MARGIN_RIGHT)
    self._plot_height = h - (MARGIN_TOP + MARGIN_BOTTOM)

    if self._id is not None:
      drawtext(qp, MARGIN_LEFT+self._plot_width/2, 10, self._id,
               fontSize=16, fontWeight=QtGui.QFont.Bold)

    # Set pixel positions of markers and selected region for
    # use in mouse events.
    for m in self._markers: m[0] = self._time_to_pos(m[1])
    if self._selectstart is not None:
      self._selectend[0] = self._time_to_pos(self._selectend[1])
      self._selectstart[0] = self._time_to_pos(self._selectstart[1])

    # Set plotting region as (0, 0) to (1, 1) with origin at bottom left
    qp.translate(MARGIN_LEFT, MARGIN_TOP + self._plot_height)
    qp.scale(self._plot_width, -self._plot_height)
    qp.setClipRect(0, 0, 1, 1)
    qp.setClipping(False)
    qp.setPen(QtGui.QPen(gridMajorColour, 0))
    qp.drawRect(0, 0, 1, 1)

    labelxfm = qp.transform()       # before time transforms

    # Now transform to time co-ordinates
    qp.scale(1.0/(self._end - self._start), 1.0)
    qp.translate(-self._start, 0.0)
    self._showSelectionRegion(qp)   # Highlight selected region
    self._showAnnotations(qp)       # Show annotations
    self._showSelectionTimes(qp)    # Time labels on top of annotation bars
    self._showTimeMarkers(qp)       # Position markers
    self._draw_time_grid(qp)

    # Draw each each visible trace
    plots = [ p[2] for p in self._plotlist if p[1] ]
    gridheight = 0
    for plot in plots: gridheight += plot.gridheight
    plotposition = gridheight
    try:
      labelfreq = int(10.0/(float(self._plot_height)/(gridheight + 1))) + 1
    except ZeroDivisionError:
      labelfreq = 0
    for plot in plots:
      qp.save()
      qp.scale(1.0, float(plot.gridheight)/gridheight)
      plotposition -= plot.gridheight
      qp.translate(0.0, float(plotposition)/plot.gridheight)
      plot.drawTrace(qp, self._start, self._end,
        labelfreq=labelfreq,
        markers=[m[1] for m in self._markers])
      qp.restore()
    # Event labels have now been assigned (by drawTrace())
    # so can show them
    qp.setTransform(labelxfm)
    self._draw_plot_labels(qp)
    qp.end()                     # Done all drawing

  def _draw_plot_labels(self, painter):
  #-----------------------------------
    plots = [ p[2] for p in self._plotlist if p[1] ]
    gridheight = 0
    for plot in plots: gridheight += plot.gridheight
    plotposition = gridheight
    for plot in plots:
      painter.save()
      painter.scale(1.0, float(plot.gridheight)/gridheight)
      plotposition -= plot.gridheight
      painter.translate(0.0, float(plotposition)/plot.gridheight)
      painter.setPen(QtGui.QPen(textColour, 0))
      drawtext(painter, (MARGIN_LEFT-40)/2, 0.5, plot.label, mapX=False)  # Signal label
      for n, m in enumerate(self._markers):
        ytext = plot.yPosition(m[0])
        if ytext is not None:                             # Write event descriptions on RHS
          painter.setPen(QtGui.QPen(markerColour if n == 0 else marker2Colour, 0))
          drawtext(painter, MARGIN_LEFT+self._plot_width+25, 0.50, ytext, mapX=False)
      painter.restore()

  def _showSelectionRegion(self, painter):
  #---------------------------------------
    if self._selectstart != self._selectend:
      duration = (self._selectend[1] - self._selectstart[1])
      painter.setClipping(True)
      painter.fillRect(QtCore.QRectF(self._selectstart[1], 0.0, duration, 1.0), selectionColour)
      painter.setPen(QtGui.QPen(selectEdgeColour, 0))
      painter.drawLine(QtCore.QPointF(self._selectstart[1], 0), QtCore.QPointF(self._selectstart[1], 1.0))
      painter.drawLine(QtCore.QPointF(self._selectend[1],   0), QtCore.QPointF(self._selectend[1],   1.0))
      painter.setClipping(False)

  def _showSelectionTimes(self, painter):
  #--------------------------------------
    if self._selectstart != self._selectend:
      duration = (self._selectend[1] - self._selectstart[1])
      ypos = MARGIN_TOP - 8
      painter.setPen(QtGui.QPen(selectTimeColour, 0))
      drawtext(painter, self._selectstart[1], ypos, str(self._selectstart[1]), mapY=False)
      drawtext(painter, self._selectend[1],   ypos, str(self._selectend[1]),   mapY=False)
      painter.setPen(QtGui.QPen(selectLenColour, 0))
      middle = (self._selectend[1] + self._selectstart[1])/2.0
      if duration < 0: duration = -duration
      drawtext(painter, middle, ypos, str(duration), mapY=False)

  def _draw_time_grid(self, painter):
  #----------------------------------
    xfm = painter.transform()
    painter.resetTransform()
    ypos = MARGIN_TOP + self._plot_height
    painter.setPen(QtGui.QPen(gridMinorColour, 0))
    t = self._timeRange.start
    while t <= self._end:
      if self._start <= t <= self._end:
        painter.drawLine(QtCore.QPoint(self._time_to_pos(t), MARGIN_TOP),
          QtCore.QPoint(self._time_to_pos(t), ypos))
      t += self._timeRange.minor
    t = self._timeRange.start
    while t <= self._end:
      if self._start <= t <= self._end:
        painter.setPen(QtGui.QPen(gridMajorColour, 0))
        painter.drawLine(QtCore.QPoint(self._time_to_pos(t), MARGIN_TOP),
          QtCore.QPoint(self._time_to_pos(t), ypos+5))
        painter.setPen(QtGui.QPen(textColour, 0))
        drawtext(painter, self._time_to_pos(t), ypos+18, str(t),
          mapX=False, mapY=False)
      t += self._timeRange.major
    drawtext(painter, MARGIN_LEFT+self._plot_width+40, ypos+18,
             'Time\n(secs)', mapX=False, mapY=False)
    painter.setTransform(xfm)

  def _setTimeGrid(self, start, end):
  #----------------------------------
    self._timeRange = NumericRange(start, end)
    self._start = start
    self._end = end

  def _showTimeMarkers(self, painter):
  #-----------------------------------
    xfm = painter.transform()
    painter.resetTransform()
    for n, m in enumerate(self._markers):
      ypos = MARGIN_TOP - 20
      painter.setPen(QtGui.QPen(markerColour if n == 0 else marker2Colour, 0))
      painter.drawLine(QtCore.QPoint(m[0], ypos + 6),
        QtCore.QPoint(m[0], MARGIN_TOP+self._plot_height+10))
      drawtext(painter, m[0], ypos, str(self._timeRange.map(m[1])),
        mapX=False, mapY=False)
      if n > 0 and m[1] != last[1]:
        painter.setPen(QtGui.QPen(textColour, 0))
        width = self._timeRange.map(last[1]) - self._timeRange.map(m[1])
        if width < 0: width = -width
        drawtext(painter, (last[0]+m[0])/2.0, ypos, str(width),
          mapX=False, mapY=False)
      last = m
    painter.setTransform(xfm)

  def _showAnnotations(self, painter):
  #-----------------------------------
    xfm = painter.transform()
    painter.resetTransform()
    right_side = MARGIN_LEFT + self._plot_width
    line_space = ANN_LINE_WIDTH + ANN_LINE_GAP
    # Sort (into time order), start from top, and not
    # step down if prev. end <= new start
    # Save bar rectangle for finding tool tip...
    self._annrects = []      # list if (rect, id) pairs
    endtimes = []            # [endtime, colour] pair for each row
    nextcolour = 0
    colourdict = {}          # key by text, to use the same colour for the same text
    for ann, id in sorted([ (ann, id)
                            for id, ann in self._annotations.items() ]):
      row = None
      colours = [ None, None, None ]   # On left, above, below
      for n, e in enumerate(endtimes):
        if ann[0] > e[0]:     # Start time after last end on this row?
          row = n
          e[0] = ann[1]       # Save end time
          colours[0] = e[1]
          if (n + 1) < len(endtimes):
            colours[2] = endtimes[n+1][1]
          break
        colours[1] = e[1]
      if row is None:
        row = len(endtimes)
        endtimes.append([ann[1], None])
      ann_top = ANN_START + row*line_space
      text = self._annotation_display_text(ann)
      thiscolour = colourdict.get(text, None)
      if thiscolour is None:
        used = -1
        l = len(ANN_COLOURS)
        used = [ c for c in colours if c is not None ]
        thiscolour = nextcolour
        while thiscolour in used:      # Must terminate since len(ANN_COLOURS) > len(used)
          thiscolour = (thiscolour + 1) % len(ANN_COLOURS)
        nextcolour = (nextcolour + 1) % len(ANN_COLOURS)
        colourdict[text] = thiscolour
      endtimes[row][1] = thiscolour  # Save colour index
      colour = ANN_COLOURS[thiscolour]
      pen = QtGui.QPen(colour, 0)
#      pen.setCapStyle(QtCore.Qt.FlatCap)
#      pen.setWidth(1)
      painter.setPen(pen)
      xstart = self._time_to_pos(ann[0])
      xend = self._time_to_pos(ann[1])
      if MARGIN_LEFT < xstart < right_side:
        painter.drawLine(QtCore.QPoint(xstart, ann_top),
                         QtCore.QPoint(xstart, MARGIN_TOP+self._plot_height))
      if MARGIN_LEFT < xend < right_side:
        painter.drawLine(QtCore.QPoint(xend, ann_top),
                         QtCore.QPoint(xend, MARGIN_TOP+self._plot_height))
      if xstart < right_side and MARGIN_LEFT < xend:
        left = max(MARGIN_LEFT, xstart)
        right = min(xend, right_side)
        width = right - left
        if width <= 1:                     ##  Instants
          left -= 2
          width = 4
        rect = QtCore.QRect(left, ann_top, ##  - ANN_LINE_WIDTH/2,
                            width, ANN_LINE_WIDTH)
#        pen.setWidth(ANN_LINE_WIDTH)
#        painter.setPen(pen)
        painter.fillRect(rect, colour)
        self._annrects.append((rect, id))
    painter.setTransform(xfm)

  def _pos_to_time(self, pos):
  #---------------------------  
    time = self._start + float(self._duration)*(pos - MARGIN_LEFT)/self._plot_width
    if time < self._start: time = self._start
    if time > self._end: time = self._end
    return self._timeRange.map(time)

  def _time_to_pos(self, time):
  #---------------------------  
    return MARGIN_LEFT + (time - self._start)*self._plot_width/float(self._duration)

  @pyqtSlot(float, float)
  def setTimeRange(self, start, duration):
  #---------------------------------------
    self.start = self._start = start
    self.end = self._end = start + duration
    self.duration = duration
    self.setTimeZoom(self._timezoom)    # Keep existing zoom
    self._markers = [ [0, self._start], [0, self._start] ]  ##  Two markers

  def setTimeZoom(self, scale):
  #----------------------------
    self._timezoom = scale
    self._duration = self.duration/scale
    newstart = (self._start + self._end - self._duration)/2.0
    newend = newstart + self._duration
    if newstart < self.start:
      newstart = self.start
      newend = newstart + self._duration
    elif newend > self.end:
      newend = self.end
      newstart = newend - self._duration
    # Now update slider's position to reflect _start _position _end
    self._setTimeGrid(newstart, newend)
    #for m in self._markers: m[0] = self._time_to_pos(m[1])
    self.update()

  def setTimeScroll(self, scrollbar):
  #----------------------------------
    scrollbar.setMinimum(0)
    scrollwidth = 1000
    scrollbar.setPageStep(scrollwidth/self._timezoom)
    scrollbar.setMaximum(scrollwidth - scrollbar.pageStep())
    scrollbar.setValue(scrollwidth*(self._start - self.start)/float(self.duration))

  def moveTimeScroll(self, scrollbar):
  #-----------------------------------
    start = (self.start
           + scrollbar.value()*float(self.duration)/(scrollbar.maximum()+scrollbar.pageStep()))
    self._setTimeGrid(start, start + self._duration)
#    for m in self._markers:                       ## But markers need to scroll...
#      if m[1] < self._start: m[1] = self._start
#      if m[1] > self._end: m[1] = self._end
    self.update()

  @pyqtSlot(float)
  def setMarker(self, time):
  #-------------------------
    self._markers[0][0] = self._time_to_pos(time)
    self._markers[0][1] = self._timeRange.map(time)

  def mousePressEvent(self, event):
  #--------------------------------
    self._mousebutton = event.button()
    if self._mousebutton != QtCore.Qt.LeftButton: return
    pos = event.pos()
    xpos = pos.x()
    xtime = self._pos_to_time(xpos)
    # check right click etc...
    marker = None
    if pos.y() <= MARGIN_TOP:
      mpos = sorted([ (m[0], n) for n, m in enumerate(self._markers) ])
      if   xpos <= mpos[0][0]:
        self._marker = mpos[0][1]
      elif xpos >= mpos[-1][0]:
        self._marker = mpos[-1][1]
      else:
        for n, m in enumerate(mpos[:-1]):
          mid = (m[0] + mpos[n+1][0])/2.0
          if xpos <= mid:
            self._marker = m[1]
            break
          elif xpos <= mpos[n+1][0]:
            self._marker = mpos[n+1][1]
            break ;
      marker = self._markers[self._marker]
    else:
      for n, m in enumerate(self._markers):
        if (xpos-2) <= m[0] <= (xpos+2):
          self._marker = n
          marker = m
          break
    if marker:
      marker[0] = xpos
      marker[1] = xtime
    elif MARGIN_TOP < pos.y() <= (MARGIN_TOP + self._plot_height):
## Need to be able to clear selection (click inside??)
## and start selecting another region (drag outside of region ??)
      if self._selectstart is None:
        self._selectstart = [xpos, xtime]
        self._selectend = self._selectstart
      elif (xpos-2) <= self._selectstart[0] <= (xpos+2):
        end = self._selectend                       # Start edge move
        self._selectend = self._selectstart
        self._selectstart = end
      elif ((self._selectstart[0]+2) < xpos < (self._selectend[0]-2)
         or (self._selectend[0]+2) < xpos < (self._selectstart[0]-2)):
        self._selectmove = xpos
      elif not ((xpos-2) <= self._selectend[0] <= (xpos+2)):
        self._selectstart = [xpos, xtime]
        self._selectend = self._selectstart
      self._selecting = True
    self.update()

  def _annotation_display_text(self, ann):
  #---------------------------------------
    text = [ ]
    if ann[2] != '':
      text.append("<p>%s</p>" % ann[2])
    if ann[3] not in [ None, [ ] ]:
      text.append("<p>Tags: %s</p>"
        % ', '.join(sorted([self.semantic_tags.get(str(t), str(t)) for t in ann[3]])))
    return ''.join(text)

  def mouseMoveEvent(self, event):
  #-------------------------------
    xpos = event.pos().x()
    ypos = event.pos().y()
    xtime = self._pos_to_time(xpos)
    tooltip = False
    if self._mousebutton is None:
      for a in self._annrects:
        if a[0].contains(xpos, ypos):
          font = QtWidgets.QToolTip.font()
          font.setPointSize(16)
          QtWidgets.QToolTip.setFont(font)
          QtWidgets.QToolTip.showText(event.globalPos(),
            self._annotation_display_text(self._annotations[a[1]]))
          tooltip = True
          break
    elif self._marker >= 0:
      self._markers[self._marker][0] = xpos
      self._markers[self._marker][1] = xtime
      self.update()
    elif self._selecting:
      if self._selectmove is None:
        self._selectend = [xpos, xtime]
      else:
        delta = xpos - self._selectmove
        self._selectmove = xpos
        self._selectend[0] += delta
        self._selectend[1] = self._timeRange.map(self._selectend[0])
        self._selectstart[0] += delta
        self._selectstart[1] = self._timeRange.map(self._selectstart[0])
      self.update()
    if not tooltip: QtWidgets.QToolTip.showText(event.globalPos(), '')

  def mouseReleaseEvent(self, event):
  #----------------------------------
    if self._mousebutton == QtCore.Qt.LeftButton:
      self._marker = -1
      if self._selecting:
        if self._selectstart[0] > self._selectend[0]: # Moved start edge
          end = self._selectend
          self._selectend = self._selectstart
          self._selectstart = end
        self._selecting = False
        self._selectmove = None
    self._mousebutton = None

  def contextMenu(self, pos):
  #--------------------------
    self._mousebutton = None
    for a in self._annrects:
      if a[0].contains(pos):
        ann_id = a[1]
        ann = self._annotations[ann_id]
        if ann[4]:  # editable
          menu = QtWidgets.QMenu()
          menu.addAction("Edit")
          menu.addAction("Delete")
          item = menu.exec_(self.mapToGlobal(pos))
          if item:
            if item.text() == 'Edit':
              dialog = AnnotationDialog(self._id, ann[0], ann[1], text=ann[2], tags=ann[3], parent=self)
              if dialog.exec_():
                text = str(dialog.get_annotation()).strip()
                tags = dialog.get_tags()
                if (text and text != str(ann[2]).strip() or tags != ann[3]):
                  self.annotationModified.emit(ann_id, text, tags)
            elif item.text() == 'Delete':
              confirm = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question, "Delete Annotation",
                "Delete Annotation", QtWidgets.QMessageBox.Cancel | QtWidgets.QMessageBox.Ok)
              confirm.setInformativeText("Do you want to delete the annotation?")
              confirm.setDefaultButton(QtWidgets.QMessageBox.Cancel)
              if confirm.exec_() == QtWidgets.QMessageBox.Ok:
                self.annotationDeleted.emit(ann_id)
        return
    if (MARGIN_TOP < pos.y() <= (MARGIN_TOP + self._plot_height)
     and MARGIN_LEFT < pos.x() <= (MARGIN_LEFT + self._plot_width)):
      menu = QtWidgets.QMenu()
      if (self._selectstart != self._selectend
       and self._selectstart[0] < pos.x() < self._selectend[0]):
        menu.addAction("Zoom")
        menu.addAction("Annotate")
##        menu.addAction("Export")
        item = menu.exec_(self.mapToGlobal(pos))
        if item:
          clearselection = False
          if item.text() == 'Zoom':
            scale = self.duration/(self._selectend[1] - self._selectstart[1])
            self._start = self._selectstart[1]
            self._end   = self._selectend[1]
            self.zoomChart.emit(scale)    # Results in setTimeZoom() being called
            clearselection = True
          elif item.text() == 'Annotate':
            dialog = AnnotationDialog(self._id, self._selectstart[1], self._selectend[1], parent=self)
            if dialog.exec_():
              text = dialog.get_annotation()
              tags = dialog.get_tags()
              if text or tags:
                self.annotationAdded.emit(self._selectstart[1], self._selectend[1], text, tags)
                clearselection = True
          elif item.text() == 'Export':
            filename = QtWidgets.QFileDialog.getSaveFileName(self, 'Export region', '', '*.bsml')
            if filename:
              self.exportRecording.emit(filename, self._selectstart[1], self._selectend[1])
              clearselection = True
          if clearselection: self._selectend = self._selectstart
          self.update()
      else:
        menu.addAction("Save as PNG")
        item = menu.exec_(self.mapToGlobal(pos))
        if item:
          filename = QtWidgets.QFileDialog.getSaveFileName(self, 'Save chart', '', '*.png')
          if filename:
            output = QtGui.QImage(self.width(), self.height(), QtGui.QImage.Format_ARGB32_Premultiplied)
            self._draw(output)
            output.save(filename, 'PNG')


if __name__ == '__main__':
#=========================

  import sys
  import math

  logging.basicConfig(format='%(asctime)s %(levelname)8s %(threadName)s: %(message)s')
  logging.getLogger().setLevel('DEBUG')


  from biosignalml.data import UniformTimeSeries

  app = QtWidgets.QApplication(sys.argv)

  chart = ChartPlot()
  chart.addSignalPlot('1', 'label', 'units')
  points = 1000
  tsdata = np.fromfunction(lambda x: np.sin(2.0*np.pi*x/points), (points+1,))
  print(tsdata)
  data = DataSegment(0.0, UniformTimeSeries(tsdata, rate=1))
  chart.setTimeRange(0.0, float(points))
  chart.appendData('1', data)
  chart.show()


  sys.exit(app.exec_())
