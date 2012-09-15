from PyQt4 import QtCore, QtGui

from tgrid import Ui_Form


class TermGrid(QtGui.QFrame):
#==============================

  sizeChanged = QtCore.pyqtSignal(int)

  def __init__(self, parent=None):
  #-------------------------------
    QtGui.QWidget.__init__(self, parent)
    self.ui = Ui_Form()
    self.ui.setupUi(self)
    self.setPalette(
      QtGui.QPalette(QtGui.QColor(200, 200, 255), QtGui.QColor(240, 255, 240))
      )
    self._rows = [ (self.ui.property, self.ui.relation, self.ui.valuelist, self.ui.operation) ]
    self._names = [ c.objectName() for c in self._rows[0] ]
    self._active_rows = 1
    self.setup_last_row()
    self._config = None


  def set_configuration(self, config):
  #-----------------------------------
    """
    Set configuartion information.

    This method should be called as part of initialistion.
    """
    self._config = config
    if self._config:
      for p in self._config.properties():
        self.ui.property.addItem(p)


  def show_row(self, row):
  #-----------------------
    for c in self._rows[row][1:]:
      c.show()
    if row >= 2: c.hide()        ## Can't add more rows


  def setup_last_row(self):
  #------------------------
    row = len(self._rows) - 1
    for n, c in enumerate(self._rows[row]):
      c.row = row
      if n > 0: c.hide()
      else:
        c.insertItem(0, 'Please select:')
        c.setCurrentIndex(0)
        c.currentIndexChanged.connect(self.on_property_changed)
    c.setItemText(0, 'More...')  ## Last row's operation
    c.currentIndexChanged.connect(self.on_operation_changed)


  def on_operation_changed(self, index):
  #-------------------------------------
    row = QtCore.QObject.sender(self).row
    lastrow = (row == len(self._rows) - 1)
    if index == 0 and not lastrow: 
      for c in self._rows[row][:-1]:
##        self.ui.gridLayout.removeWidget(c)
        c.hide()
##        del c
      self._active_rows -= 1
      c = self._rows[row][-1]
      c.clear()
      c.addItem('Ignored')
    elif index > 0 and lastrow and row < 2:
      nextrow = [ ]
      next = len(self._rows)
      lastitem = len(self._rows[0]) - 1
      for n, c in enumerate(self._rows[row]):
        item = c.clone('%s%d' % (self._names[n], next), n in [0, lastitem])
        col = n if n < lastitem else (n + 1)
        self.ui.gridLayout.addWidget(item, next, col)
        nextrow.append(item)
      c.setItemText(0, 'Ignore')  ## Change current row's operation
      self._rows.append(tuple(nextrow))
      self._active_rows += 1
      self.setup_last_row()
      height = 30*self._active_rows
      self.ui.gridLayout.invalidate()
#      self.ui.layoutWidget.resize(self.ui.layoutWidget.width(), height)
#      self.resize(self.width(), height)
#      self.sizeChanged.emit(height)
    self.update()


  def on_property_changed(self, index):
  #------------------------------------
    p = QtCore.QObject.sender(self)
    text = p.currentText()
    if index > 0 and str(p.itemText(0)).startswith('Please'):
      p.removeItem(0)
      self.show_row(p.row)
    reln = self._rows[p.row][1]
    reln.clear()
    values = self._rows[p.row][2]
    values.clear()
    if self._config:
      for r in self._config.relations(text):
        reln.addItem(r)
      valuelist = self._config.values(text)
      if isinstance(valuelist, list):
        values.addItem('Please select:')
        for v in valuelist: values.addItem(v)
      else:
        pass
        # Need to replace (row, 2) with text input box
        # And update _row[p.row][2] as ignore hides
        # but what about clone...
        # why not save a copy of initial widgets for cloning??


  def clone(self, name):
  #---------------------
    copy = self.__class__(self.parentWidget())
    copy.setSizePolicy(self.sizePolicy())
    copy.setMinimumSize(self.minimumSize())
    copy.setMaximumSize(self.maximumSize())
    copy.setFrameShape(self.frameShape())
    copy.setFrameShadow(self.frameShadow())
    copy.setObjectName(name)
    return copy
