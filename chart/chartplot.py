import math
import logging
import numpy as np

from PyQt4 import QtCore, QtGui
from PyQt4 import QtOpenGL

##ChartWidget = QtGui.QWidget       # Hangs if > 64K points
ChartWidget = QtOpenGL.QGLWidget    # Faster, anti-aliasing not quite as good QWidget


# Margins of plotting region within chart, in pixels
MARGIN_LEFT   = 110
MARGIN_RIGHT  = 80
MARGIN_TOP    = 30
MARGIN_BOTTOM = 40


traceColour      = QtGui.QColor('green')
selectedColour   = QtGui.QColor('red')
textColour       = QtGui.QColor('darkBlue')
markerColour     = QtGui.QColor('red')
marker2Colour    = QtGui.QColor(0xCC, 0x55, 0x00)  ## 'burnt orange'
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
    self.selected = False
    self._points = [ ]
    self._path = None
    self._lastpoint = None
    self._ymin = ymin
    self._ymax = ymax
    if data: self.appendData(data, ymin, ymax)
    else:    self._setYrange()

  def _setYrange(self):
  #--------------------
    if self._ymin == self._ymax:
      if self._ymin: (ymin, ymax) = (self._ymin-abs(self._ymin)/2.0, self._ymax+abs(self._ymax)/2.0)
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

  def appendData(self, data, ymin=None, ymax=None):
  #------------------------------------------------
    if ymin is None: ymin = np.amin(data.data)
    if ymax is None: ymax = np.amax(data.data)
    if self._ymin == None or self._ymin > ymin: self._ymin = ymin
    if self._ymax == None or self._ymax < ymax: self._ymax = ymax
    self._setYrange()
    if self._path is None:
      self._path = QtGui.QPainterPath()
    else:
      self._path.lineTo(QtCore.QPointF(data[0][0], data[0][1]))
    trace = [ QtCore.QPointF(pt[0], pt[1]) for pt in data.points ]
    self._path.addPolygon(QtGui.QPolygonF(trace))
    self._points.extend(trace) ## for yValue lookup

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
    painter.scale(1.0, 1.0/(self.ymax - self.ymin))
    painter.translate(0.0, -self.ymin)
    # draw and label y-gridlines.
    n = 0
    y = self.ymin
    while y <= self.ymax:
      painter.setPen(QtGui.QPen(gridMinorColour))
      painter.drawLine(QtCore.QPointF(start, y), QtCore.QPointF(end, y))
      if (endlabels or self.ymin < y < self.ymax) and (n % labelfreq) == 0:
        painter.drawLine(QtCore.QPointF(start-0.005*(end-start), y), QtCore.QPointF(start, y))
        painter.setPen(QtGui.QPen(textColour))
        drawtext(painter, MARGIN_LEFT-20, y, str(y), mapX=False)    # Label grid
      y += self.gridstep
      if -1e-10 < y < 1e-10: y = 0.0  #####
      n += 1
    painter.setClipping(True)
    painter.setPen(QtGui.QPen(traceColour if not self.selected else selectedColour))
    # Could find start/end indices and only draw segment
    # rather than rely on clipping...
    painter.drawPath(self._path)
    #painter.drawPolyline(QtGui.QPolygonF(self._points))
    # But very fast as is, esp. when using OpenGL

    if markers:
      xfm = painter.transform()
      for n, t in enumerate(markers):
         painter.setPen(QtGui.QPen(markerColour if n == 0 else marker2Colour))
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
  def __init__(self, label, mapping=lambda x: (str(x), str(x)), data=None):
  #------------------------------------------------------------------------
    self.label = label
    self.selected = False
    self._mapping = mapping
    self._events = [ ]
    self._eventpos = []
    self.gridheight = 2   ###
    if data: self.appendData(data)

  def yValue(self, time):
  #----------------------
    return None

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
    self._events.extend([ (pt[0], self._mapping(pt[1])) for pt in data.points ])

  def drawTrace(self, painter, start, end, markers=None, **kwds):
  #--------------------------------------------------------------
    painter.setClipping(True)
    self._eventpos = []
    for t, event in self._events:
      if event[0]:
        painter.setPen(QtGui.QPen(traceColour if not self.selected else selectedColour))
        painter.drawLine(QtCore.QPointF(t, 0.0), QtCore.QPointF(t, 1.0))
        painter.setPen(QtGui.QPen(textColour))
        drawtext(painter, t, 0.5, event[0])
        xy = painter.transform().map(QtCore.QPointF(t, 0.5))
        self._eventpos.append( (int(xy.x()+0.5), int(xy.y()+0.5), '\n'.join(event[1].split())) )


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
    self._plots = {}        # id --> index in plotlist
    self._plotlist = []     # [id, visible, plot] triples as a list
    self._timezoom = 1.0
    self._markers = []  # List of [xpos, time] pairs
    self._marker = -1   # Index of marker being dragged
    self._selectstart = None
    self._selectend = None
    self._selecting = False
    self._selectmove = None

  def setTimeRange(self, start, duration):
  #---------------------------------------
    self.start = start
    self.end = start + duration
    self.duration = duration
    self._setTimeGrid(self.start, self.end)
    self._duration = self.duration
    self._markers = [ [0, self._start], [0, self.start] ]  ##  Two markers

  def addSignalPlot(self, id, label, units, visible=True, data=None, ymin=None, ymax=None):
  #----------------------------------------------------------------------------------------
    plot = SignalPlot(label, units, data, ymin, ymax)
    self._plots[str(id)] = len(self._plotlist)
    self._plotlist.append([str(id), visible, plot])
    self.update()

  def addEventPlot(self, id, label, mapping=lambda x: str(x), visible=True, data=None):
  #------------------------------------------------------------------------------------
    plot = EventPlot(label, mapping, data)
    self._plots[str(id)] = len(self._plotlist)
    self._plotlist.append([str(id), visible, plot])
    self.update()

  def appendData(self, id, data):
  #------------------------------
    n = self._plots.get(str(id), -1)
    if n >= 0:
      self._plotlist[n][2].appendData(data)
      self.update()

  def setPlotVisible(self, id, visible=True):
  #------------------------------------------
    n = self._plots.get(str(id), -1)
    if n >= 0:
      self._plotlist[n][1] = visible
      self.update()

  def plotOrder(self):
  #-------------------
    """ Get list of plot ids in display order. """
    return [ p[0] for p in self._plotlist ]

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

  def plotSelected(self, row):
  #---------------------------
    for n, p in enumerate(self._plotlist):
      p[2].selected = (n == row)
    self.update()

  def resizeEvent(self, e):
  #-----------------------
    self.chartPosition.emit(self.pos().x() + MARGIN_LEFT,
                            self.width() - (MARGIN_LEFT + MARGIN_RIGHT),
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
    self._plot_width  = w - (MARGIN_LEFT + MARGIN_RIGHT)
    self._plot_height = h - (MARGIN_TOP + MARGIN_BOTTOM)
    qp.translate(MARGIN_LEFT, MARGIN_TOP + self._plot_height)
    qp.scale(self._plot_width, -self._plot_height)

    for m in self._markers: m[0] = self._time_to_pos(m[1])
    if self._selectstart is not None:
      self._selectend[0] = self._time_to_pos(self._selectend[1])
      self._selectstart[0] = self._time_to_pos(self._selectstart[1])

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

    # Position markers
    for n, m in enumerate(self._markers):
      qp.setPen(QtGui.QPen(markerColour if n == 0 else marker2Colour))
      qp.drawLine(QtCore.QPointF(m[1], -0.05), QtCore.QPointF(m[1], 1.05))
      drawtext(qp, m[1], 10, '%.5g' % m[1], mapY=False)  #### WATCH...!!
      if n > 0 and m[1] != last[1]:
        qp.setPen(QtGui.QPen(textColour))
        width = last[1] - m[1]
        if width < 0: width = -width
        drawtext(qp, (last[1]+m[1])/2.0, 10, '%.5g' % width, mapY=False)  #### WATCH...!!
      last = m

    # Draw each each visible trace
    plots = [ p[2] for p in self._plotlist if p[1] ]
    gridheight = 0
    for plot in plots: gridheight += plot.gridheight
    plotposition = gridheight
    labelfreq = 10/(self._plot_height/(gridheight + 1)) + 1
    for plot in plots:
      qp.save()
      qp.scale(1.0, float(plot.gridheight)/gridheight)
      plotposition -= plot.gridheight
      qp.translate(0.0, float(plotposition)/plot.gridheight)
      plot.drawTrace(qp, self._start, self._end,
        labelfreq = labelfreq,
        markers=[m[1] for m in self._markers])
      qp.restore()
    # Done all drawing
    qp.end()


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
      painter.setPen(QtGui.QPen(textColour))
      drawtext(painter, (MARGIN_LEFT-40)/2, 0.5, plot.label, mapX=False)  # Signal label
      for n, m in enumerate(self._markers):
        ytext = plot.yPosition(m[0])
        if ytext is not None:                             # Write event descriptions on RHS
          painter.setPen(QtGui.QPen(markerColour if n == 0 else marker2Colour))
          drawtext(painter, MARGIN_LEFT+self._plot_width+25, 0.50, ytext, mapX=False)
      painter.restore()

  def _mark_selection(self, painter):
  #----------------------------------
    if self._selectstart != self._selectend:
      duration = (self._selectend[1] - self._selectstart[1])
      painter.setClipping(True)
      painter.fillRect(QtCore.QRectF(self._selectstart[1], 0.0, duration, 1.0), selectionColour)
      painter.setPen(QtGui.QPen(selectEdgeColour))
      painter.drawLine(QtCore.QPointF(self._selectstart[1], 0), QtCore.QPointF(self._selectstart[1], 1.0))
      painter.drawLine(QtCore.QPointF(self._selectend[1],   0), QtCore.QPointF(self._selectend[1],   1.0))
      painter.setClipping(False)
      painter.setPen(QtGui.QPen(textColour))
      drawtext(painter, self._selectstart[1], 22, '%.5g' % self._selectstart[1], mapY=False)  #### WATCH...!!
      drawtext(painter, self._selectend[1],   22, '%.5g' % self._selectend[1],   mapY=False)  #### WATCH...!!
      painter.setPen(QtGui.QPen(selectEdgeColour))
      middle = (self._selectend[1] + self._selectstart[1])/2.0
      if duration < 0: duration = -duration
      drawtext(painter, middle, 22, '%.5g' % duration, mapY=False)  #### WATCH...!!

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
    time = self._start + float(self._duration)*(pos - MARGIN_LEFT)/self._plot_width
    if time < self._start: time = self._start
    if time > self._end: time = self._end
    return time

  def _time_to_pos(self, time):
  #---------------------------  
    return MARGIN_LEFT + (time - self._start)*self._plot_width/float(self._duration)

  def setTimeZoom(self, scale):
  #----------------------------
    self._timezoom = scale
    self._duration = self.duration/scale
    newstart = (self.start + self.end - self._duration)/2.0
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
    #self._markerpos = self._time_to_pos(self._position)   # Done in paint()
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
    for m in self._markers:                       ## But markers need to scroll...
      if m[1] < self._start: m[1] = self._start
      if m[1] > self._end: m[1] = self._end
    self.update()

  def mousePressEvent(self, event):
  #--------------------------------
    pos = event.pos()
    xpos = pos.x()
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
      marker[1] = self._pos_to_time(marker[0])
    elif MARGIN_TOP < pos.y() <= (MARGIN_TOP + self._plot_height):
## Need to be able to clear selection (click inside??)
## and start selecting another region (drag outside of region ??)
      if self._selectstart is None:
        self._selectstart = [xpos, self._pos_to_time(xpos)]
        self._selectend = self._selectstart
      elif (xpos-2) <= self._selectstart[0] <= (xpos+2):
        end = self._selectend
        self._selectend = self._selectstart
        self._selectstart = end
      elif ((self._selectstart[0]+2) < xpos < (self._selectend[0]-2)
         or (self._selectend[0]+2) < xpos < (self._selectstart[0]-2)):
        self._selectmove = xpos
      elif not ((xpos-2) <= self._selectend[0] <= (xpos+2)):
        self._selectstart = [xpos, self._pos_to_time(xpos)]
        self._selectend = self._selectstart
      self._selecting = True
    self.update()

  def mouseMoveEvent(self, event):
  #-------------------------------
    xpos = event.pos().x()
    if self._marker >= 0:
      self._markers[self._marker][0] = xpos
      self._markers[self._marker][1] = self._pos_to_time(xpos)
    elif self._selecting:
      if self._selectmove is None:
        self._selectend = [xpos, self._pos_to_time(xpos)]
      else:
        delta = xpos - self._selectmove
        self._selectmove = xpos
        self._selectend[0] += delta
        self._selectend[1] = self._pos_to_time(self._selectend[0])
        self._selectstart[0] += delta
        self._selectstart[1] = self._pos_to_time(self._selectstart[0])
    self.update()

  def mouseReleaseEvent(self, event):
  #----------------------------------
    self._marker = -1
    self._selecting = False
    self._selectmove = None

  def contextMenu(self, pos):
  #--------------------------
    menu = QtGui.QMenu()
    menu.addAction("Zoom")
    menu.addAction("Annotate")
    menu.addAction("Export")
    selected = menu.exec_(self.mapToGlobal(pos))
    if selected:
      print selected.text()
