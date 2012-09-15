from PyQt4 import QtCore, QtGui

from tgrid import Ui_Form
from combobox import ComboBox


# Offsets into self._widgets
PROPERTY  = 0
RELATION  = 1
VALUE     = 2
OPERATION = 3
VALUETEXT = 4


class LineEdit(QtGui.QLineEdit):
#===============================

  def clone(self, name):
  #---------------------
    copy = self.__class__(self.parentWidget())
    copy.setSizePolicy(self.sizePolicy())
    copy.setObjectName(name)
    return copy


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
    self._rows = [ [self.ui.property, self.ui.relation, self.ui.valuelist, self.ui.operation] ]
    self._names = [ c.objectName() for c in self._rows[0] ]
    self._active_rows = 1
    self.setup_last_row()
    self._config = None
    self._widgets = [ ]

  def set_configuration(self, config):
  #-----------------------------------
    """
    Set configuration information.

    This method should be called as part of initialistion.
    """
    if config:
      self.ui.property.addItem('Please select:')
      for p in config.properties():
        self.ui.property.addItem(p)
    # Now have property selection list so can save widgets for copying
    self._widgets = [ c.clone('%s0' % self._names[n], n in [PROPERTY, OPERATION])
                        for n, c in enumerate(self._rows[0]) ]
    valuetext = LineEdit(self._widgets[VALUE].parentWidget())
    valuetext.setSizePolicy(self._widgets[VALUE].sizePolicy())
    valuetext.setObjectName('valuetext0')
    self._widgets.append(valuetext)
    self._names.append('valuetext')
    for c in self._widgets: c.hide()
    self._config = config

  def show_row(self, row):
  #-----------------------
    for c in self._rows[row][RELATION:]:
      c.show()
    if row >= 2: c.hide()        ## Can't add more rows

  def setup_last_row(self):
  #------------------------
    row = len(self._rows) - 1
    for n, c in enumerate(self._rows[row]):
      c.row = row
      if n > PROPERTY: c.hide()
      else:
        c.setCurrentIndex(0)
        c.currentIndexChanged.connect(self.on_property_changed)
    c.setItemText(0, 'More...')  ## Last row's operation
    c.currentIndexChanged.connect(self.on_operation_changed)


  def on_operation_changed(self, index):
  #-------------------------------------
    row = QtCore.QObject.sender(self).row
    lastrow = (row == len(self._rows) - 1)
    if index == 0 and not lastrow: 
      for c in self._rows[row][:OPERATION]: c.hide()
      self._active_rows -= 1
      c = self._rows[row][OPERATION]
      c.clear()
      c.addItem('Ignored')
    elif index > 0 and lastrow and row < 2:
      nextrow = [ ]
      next = len(self._rows)
      for n, c in enumerate(self._widgets[:VALUETEXT]):
        item = c.clone('%s%d' % (self._names[n], next), n in [PROPERTY, OPERATION])
        col = n if n < OPERATION else (n + 1)
        self.ui.gridLayout.addWidget(item, next, col)
        nextrow.append(item)
      c.setItemText(0, 'Ignore')  ## Change current row's operation
      self._rows.append(nextrow)
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
    reln = self._rows[p.row][RELATION]
    reln.clear()
    values = self._rows[p.row][VALUE]
    values.clear()
    if self._config:
      for r in self._config.relations(text):
        reln.addItem(r)
      valuelist = self._config.values(text)
      if isinstance(valuelist, list):
        if not isinstance(values, ComboBox):
          values = self._widgets[VALUE].clone('%s%d' % (self._names[VALUE], p.row))
          self._rows[p.row][VALUE] = values
          self.ui.gridLayout.addWidget(values, p.row, VALUE)
        values.addItem('Please select:')
        for v in valuelist: values.addItem(v)
      else:
        if not isinstance(values, LineEdit):
          valuetext = self._widgets[VALUETEXT].clone('%s%d' % (self._names[VALUETEXT], p.row))
          self._rows[p.row][VALUE] = valuetext
          self.ui.gridLayout.addWidget(valuetext, p.row, VALUE)
    # If first time show widgets and remove selection propmpt
    if index > 0 and str(p.itemText(0)).startswith('Please'):
      p.removeItem(0)
      self.show_row(p.row)


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
