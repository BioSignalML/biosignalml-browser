import math
import logging
import numpy as np

from PyQt4 import QtCore, QtGui
from PyQt4 import QtOpenGL

##ChartWidget = QtGui.QWidget       # Hangs if > 64K points
ChartWidget = QtOpenGL.QGLWidget    # Faster, anti-aliasing not quite as good QWidget


# Margins of plotting region within chart, in pixesl
margin_left   = 80
margin_right  = 60
margin_top    = 30
margin_bottom = 40


traceColour      = QtGui.QColor('green')
textColour       = QtGui.QColor('darkBlue')
markerColour     = QtGui.QColor('red')
gridMinorColour  = QtGui.QColor(128, 128, 255, 63)
gridMajorColour  = QtGui.QColor(0,     0, 128, 63)
selectionColour  = QtGui.QColor(220, 255, 255)
selectEdgeColour = QtGui.QColor(  0, 255, 255)


alignLeft        = 0x01
alignRight       = 0x02
alignCentre      = 0x03
alignTop         = 0x04
alignBottom      = 0x08
alignMiddle      = 0x0C
alignCentred     = 0x0F


def gridspacing(w):
#==================
  """
  Calculate spacing of major and minor grid points.
  
  Major spacing is selected to be either 1, 2, or 5, multipled by
  a power of ten; minor spacing is respectively 0.2, 0.5 or 1.0.

  Spacing is chosen so that around 10 major grid points span the
  interval.

  :param w: The width of the interval.
  :return: A tuple with (major, minor) spacing.
  """
  if   w < 0.0:  w = -w
  elif w == 0.0: raise ValueError("Grid cannot have zero width")
  l = math.log10(w)
  f = math.floor(l)
  x = l - f     # Normalised between 0.0 and 1.0
  scale = math.pow(10.0, f)
  if   x < 0.15: return ( 1*scale/10, 0.02*scale)  # The '/10' appears to
  elif x < 0.50: return ( 2*scale/10, 0.05*scale)  # minimise rounding errors
  elif x < 0.85: return ( 5*scale/10, 0.10*scale)
  else:          return (10*scale/10, 0.20*scale)


def drawtext(painter, x, y, text, mapX=True, mapY=True, align=alignCentred):
#---------------------------------------------------------------------------
  lines = text.split('\n')
  xfm = painter.transform()
  if mapX or mapY:
    pt = xfm.map(QtCore.QPointF(x, y))  # Assume affine mapping
    if mapX: x = pt.x()
    if mapY: y = pt.y()
  painter.resetTransform()
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
    painter.drawText(QtCore.QPointF(tx, ty), QtCore.QString.fromUtf8(t))
    ty += metrics.height()          ## lineSpacing()
  painter.setTransform(xfm)


class SignalPlot(object):
#========================
  """
  A single trace.
  """

  def __init__(self, label, units, data=None, ymin=None, ymax=None):
  #-----------------------------------------------------------------
    self.label = '%s\n(%s)' % (label, units) if units else label
    self._points = [ ]
    self._path = None
    self._lastpoint = None
    self._ymin = self._ymax = None
    if data: self.addData(data, ymin, ymax)
    else:    self._setYrange()

  def _setYrange(self):
  #--------------------
    if self._ymin == self._ymax:
      if self._ymin: (ymin, ymax) = (self._ymin-self._ymin/2.0, self._ymax+self._ymax/2.0)
      else:          (ymin, ymax) = (-0.5, 0.5)
    else:
      (ymin, ymax) = (self._ymin, self._ymax)
    self.gridstep = gridspacing(ymax - ymin)[0]
    self.ymin = self.gridstep*math.floor(ymin/self.gridstep)
    self.ymax = self.gridstep*math.ceil(ymax/self.gridstep)

  @property
  def gridheight(self):
  #--------------------
    return int(math.floor((self.ymax-self.ymin)/self.gridstep + 0.5))

  def addData(self, data, ymin=None, ymax=None):
  #---------------------------------------------
    if ymin is None: ymin = np.amin(data.data)
    if ymax is None: ymax = np.amax(data.data)
    if self._ymin == None or self._ymin > ymin: self._ymin = ymin
    if self._ymax == None or self._ymax < ymax: self._ymax = ymax
    self._setYrange()
    if self._path is None:
      self._path = QtGui.QPainterPath()
    else:
      self._path.drawTo(QtCore.QPointF(data[0][0], data[0][1]))

    trace = [ QtCore.QPointF(pt[0], pt[1]) for pt in data.points ]
    self._path.addPolygon(QtGui.QPolygonF(trace))
    self._points.extend(trace) ## for yValue

  def yValue(self, time):
  #----------------------
    """
    Find the y-value corresponding to a time.
    """
    i = self._index(time)
    if i is not None: return self._points[i].y()


  def _index(self, time):
  #----------------------
    i = 0
    j = len(self._points)
    if (time < self._points[0].x()
     or time > self._points[j-1].x()): return None
    while i < j:
      m = (i + j)//2
      if self._points[m].x() <= time: i = m + 1
      else:                          j = m
    return i - 1

  def drawTrace(self, painter, start, end, markers=None):
  #------------------------------------------------------
    """
    Draw the trace.

    :param painter: The QPainter to use for drawing.
    :param start: The leftmost position on the X-axis.
    :param end: The rightmost position on the X-axis.

    The painter has been scaled so that (0.0, 1.0) is the
    vertical plotting height.
    """
    painter.scale(1.0, 1.0/(self.ymax - self.ymin))
    painter.translate(0.0, -self.ymin)
    # draw and label y-gridlines.
    y = self.ymin
    while y <= self.ymax:
      painter.setPen(QtGui.QPen(gridMinorColour))
      painter.drawLine(QtCore.QPointF(start, y), QtCore.QPointF(end, y))
      painter.setPen(QtGui.QPen(textColour))
      drawtext(painter, margin_left-20, y, str(y), mapX=False)
      y += self.gridstep
      if -1e-10 < y < 1e-10: y = 0.0  #####
    painter.setClipping(True)
    painter.setPen(QtGui.QPen(traceColour))
    # Could find start/end indices and only draw segment
    # rather than rely on clipping...
    painter.drawPath(self._path)
    #painter.drawPolyline(QtGui.QPolygonF(self._points))
    # But very fast as is, esp. when using OpenGL

    if markers:
      painter.setPen(QtGui.QPen(markerColour))
      xfm = painter.transform()
      for t in markers:
         i = self._index(t)
         if i is not None:
           y = self._points[i].y()
           xy = xfm.map(QtCore.QPointF(t, y))
           drawtext(painter, xy.x()+5, xy.y(), str(y), mapX=False, mapY=False, align=alignLeft)



class EventPlot(object):
#=======================
  """
  A single event trace.
  """
  def __init__(self, label, mapping=lambda x: str(x), data=None):
  #--------------------------------------------------------------
    self.label = label
    self._mapping = mapping
    self._events = [ ]
    self.gridheight = 2   ###
    if data: self.addEvents(data)

  def yValue(self, time):
  #----------------------
    return None

  def addData(self, data):
  #-----------------------
    self._events.extend([ (pt[0], self._mapping(pt[1])) for pt in data.points ])

  def drawTrace(self, painter, start, end, markers=None):
  #------------------------------------------------------
    painter.setClipping(True)
    painter.setPen(QtGui.QPen(traceColour))
    for t, event in self._events:
      drawtext(painter, t, 0.5, event)


class ChartPlot(ChartWidget):
#============================
  """
  A Chart is made up of several Plots stacked vertically
  and all sharing the same X-axis (time axis).

  """

  chartPosition = QtCore.pyqtSignal(int, int, int)

  def __init__(self, parent):
  #--------------------------
    if ChartWidget == QtOpenGL.QGLWidget:
      QtOpenGL.QGLWidget.__init__(self,
        QtOpenGL.QGLFormat(QtOpenGL.QGL.SampleBuffers),
        parent)
    else:
      QtGui.QWidget.__init__(self, parent)
    self.setPalette(QtGui.QPalette(QtGui.QColor('black'), QtGui.QColor('white')))
##    self.setAutoFillBackground(True)  ##
    self.plots = []
    self._position = 0
    self._timezoom = 1.0
    self._movemarker = False
    self._markerpos = 0
    self._selecting = False
    self._selectstart = None
    self._selectend = None

  def setTimeRange(self, start, duration):
  #---------------------------------------
    self.start = start
    self.end = start + duration
    self.duration = duration
    self._setTimeGrid(self.start, self.end)
    self._duration = self.duration
    self._position = self._start  ##  + self._duration/2.0

  def addSignalPlot(self, label, units, data=None, ymin=None, ymax=None):
  #----------------------------------------------------------------------
    plot = SignalPlot(label, units, data, ymin, ymax)
    self.plots.append(plot)      ## Can now increase our size...
    self.update()
    return plot

  def addEventPlot(self, label, mapping=lambda x: str(x), data=None):
  #----------------------------------------------------------------
    plot = EventPlot(label, mapping, data)
    self.plots.append(plot)      ## Can now increase our size...
    self.update()
    return plot


  def resizeEvent(self, e):
  #-----------------------
    self.chartPosition.emit(self.pos().x() + margin_left,
                            self.width() - (margin_left + margin_right),
                            self.pos().y() + self.height())
  
  def paintEvent(self, e):
  #-----------------------
    self._draw(self)

  def save_as_png(self, filename):
  #-------------------------------
    output = QtGui.QImage(2000, 800, QtGui.QImage.Format_ARGB32_Premultiplied)
    #output = QtGui.QImage(self.width(), self.height(), QtGui.QImage.Format_ARGB32_Premultiplied)
    self._draw(output)
    output.save(filename, 'PNG')

  def _draw(self, device):
  #-----------------------
    qp = QtGui.QPainter()
    qp.begin(device)

    qp.setRenderHint(QtGui.QPainter.Antialiasing)

    # Set plotting region as (0, 0) to (1, 1) with origin at bottom left
    w = device.width()
    h = device.height()
    self._plot_width  = w - (margin_left + margin_right)
    self._plot_height = h - (margin_top + margin_bottom)
    qp.translate(margin_left, margin_top + self._plot_height)
    qp.scale(self._plot_width, -self._plot_height)

    self._markerpos = self._time_to_pos(self._position)    # Have reset markerpos here for resizes

    qp.setClipRect(0, 0, 1, 1)
    qp.setClipping(False)
    qp.setPen(QtGui.QPen(gridMajorColour))
    qp.drawRect(0, 0, 1, 1)

    # Plot labels before time transforms
    self._draw_plot_labels(qp)

    # Now transform to time co-ordinates
    qp.scale(1.0/(self._end - self._start), 1.0)
    qp.translate(-self._start, 0.0)
    self._draw_time_grid(qp)
    self._mark_selection(qp)

    # Position marker
    qp.setPen(QtGui.QPen(markerColour))
    qp.drawLine(QtCore.QPointF(self._position, -0.05), QtCore.QPointF(self._position, 1.0))
    drawtext(qp, self._position, 10, '%.5g' % self._position, mapY=False)  #### WATCH...!!

    # Draw each each trace
    gridheight = 0
    for plot in self.plots: gridheight += plot.gridheight
    plotposition = gridheight
    for plot in self.plots:
      qp.save()
      qp.scale(1.0, float(plot.gridheight)/gridheight)
      plotposition -= plot.gridheight
      qp.translate(0.0, float(plotposition)/plot.gridheight)
      plot.drawTrace(qp, self._start, self._end, markers=[self._position])
      qp.restore()

    qp.end()


  def _draw_plot_labels(self, painter):
  #-----------------------------------
    gridheight = 0
    for plot in self.plots: gridheight += plot.gridheight
    plotposition = gridheight
    for plot in self.plots:
      painter.save()
      painter.scale(1.0, float(plot.gridheight)/gridheight)
      plotposition -= plot.gridheight
      painter.translate(0.0, float(plotposition)/plot.gridheight)
      painter.setPen(QtGui.QPen(textColour))
      drawtext(painter, 20, 0.5, plot.label, mapX=False)
        painter.setPen(QtGui.QPen(markerColour))
      painter.restore()

  def _mark_selection(self, painter):
  #----------------------------------
    if self._selectstart != self._selectend:
      duration = (self._selectend - self._selectstart)
      painter.setClipping(True)
      painter.fillRect(QtCore.QRectF(self._selectstart, 0.0, duration, 1.0), selectionColour)
      painter.setPen(QtGui.QPen(selectEdgeColour))
      painter.drawLine(QtCore.QPointF(self._selectstart, 0), QtCore.QPointF(self._selectstart, 1.0))
      painter.drawLine(QtCore.QPointF(self._selectend, 0), QtCore.QPointF(self._selectend, 1.0))
      painter.setClipping(False)
      painter.setPen(QtGui.QPen(textColour))
      drawtext(painter, self._selectstart, 22, '%.5g' % self._selectstart, mapY=False)  #### WATCH...!!
      drawtext(painter, self._selectend,   22, '%.5g' % self._selectend,   mapY=False)  #### WATCH...!!
      painter.setPen(QtGui.QPen(selectEdgeColour))
      middle = (self._selectend + self._selectstart)/2.0
      drawtext(painter, middle,            22, '%.5g' % duration,          mapY=False)  #### WATCH...!!

  def _draw_time_grid(self, painter):
  #----------------------------------
    ypos = painter.paintEngine().paintDevice().height() - 15      ## Needs to track bottom of tick marks
    painter.setPen(QtGui.QPen(gridMinorColour))
    t = self._gridstart
    while t <= self._end:
      if self._start <= t <= self._end:
        painter.drawLine(QtCore.QPointF(t, 0), QtCore.QPointF(t, 1))
      t += self._Xgrid[1]
    t = self._gridstart
    while t <= self._end:
      if self._start <= t <= self._end:
        painter.setPen(QtGui.QPen(gridMajorColour))
        painter.drawLine(QtCore.QPointF(t, -0.01), QtCore.QPointF(t, 1))
        painter.setPen(QtGui.QPen(textColour))
        drawtext(painter, t, ypos, str(t), mapY=False)
      t += self._Xgrid[0]

  def _setTimeGrid(self, start, end):
  #----------------------------------
    grid = gridspacing(end - start)
    self._gridstart = grid[0]*math.floor(start/grid[0])
    self._Xgrid = grid
    self._start = start
    self._end = end

#  def setTimePos(self, position):        # 0 -- 1.0
#  #--------------------------------
##    self._position = self._start + self._duration*position
#    self.update()

  def _pos_to_time(self, pos):
  #---------------------------  
    time = self._start + float(self._duration)*(pos - margin_left)/self._plot_width
    if time < self._start: time = self._start
    if time > self._end: time = self._end
    return time

  def _time_to_pos(self, time):
  #---------------------------  
    return margin_left + (time - self._start)*self._plot_width/float(self._duration)

  def setTimeZoom(self, scale):
  #----------------------------
    self._timezoom = scale
    self._duration = self.duration/scale
    newstart = self._position - self._duration/2.0
    newend = self._position + self._duration/2.0
    if newstart < self.start:
      newstart = self.start
      newend = newstart + self._duration
    elif newend > self.end:
      newend = self.end
      newstart = newend - self._duration
    # Now update slider's position to reflect _start _position _end
    self._setTimeGrid(newstart, newend)
    self._markerpos = self._time_to_pos(self._position)
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
    if self._position < self._start: self._position = self._start
    if self._position > self._end: self._position = self._end
    self.update()

  def mousePressEvent(self, event):
  #--------------------------------
    pos = event.pos()
    # check right click etc...
    if pos.y() <= margin_top or (pos.x()-2) <= self._markerpos <= (pos.x()+2):
      self._markerpos = pos.x()
      self._position = self._pos_to_time(self._markerpos)
      self._movemarker = True
    elif margin_top < pos.y() <= (margin_top + self._plot_height):
## Need to be able to clear selection (click inside??), move boundaries (drag edges)
## and start selecting another region (drag outside of region ??)
      self._selectstart = self._pos_to_time(pos.x())
      self._selectend = self._selectstart
      self._selecting = True
    self.update()

  def mouseMoveEvent(self, event):
  #-------------------------------
    pos = event.pos()
    if self._movemarker:
      self._markerpos = pos.x()
      self._position = self._pos_to_time(self._markerpos)
    elif self._selecting:
      self._selectend = self._pos_to_time(pos.x())
      if self._selectstart > self._selectend:
        t = self._selectstart
        self._selectstart = self._selectend
        self._selectend = t
    self.update()

  def mouseReleaseEvent(self, event):
  #-------------------------------
    self._movemarker = False
    self._selecting = False

  def contextMenu(self, pos):
  #--------------------------
    menu = QtGui.QMenu()
    menu.addAction("Zoom")
    menu.addAction("Annotate")
    menu.addAction("Export")
    selected = menu.exec_(self.mapToGlobal(pos))
    if selected:
      print selected.text()
