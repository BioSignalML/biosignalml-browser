from xml.sax.saxutils import escape, quoteattr

from PyQt4 import QtCore, QtGui

from tgrid import Ui_Form
from combobox import ComboBox


# Offsets into self._widgets
PROPERTY  = 0
RELATION  = 1
VALUE     = 2
OPERATION = 3
VALUETEXT = 4

MAXROWS   = 3   #: Maximum number of terms


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
    self._activerows = 1
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
    b = c.blockSignals(True)       # To stop ourselves being triggered...
    c.setItemText(0, 'More...')    ## Last row's operation
    c.setCurrentIndex(0)
    c.currentIndexChanged.connect(self.on_operation_changed)
    c.blockSignals(b)


  def list_elements(self):
  #-----------------------
    gl = self.ui.gridLayout
    for i in xrange(gl.count()):
      itm = gl.itemAt(i)
      if isinstance(itm, QtGui.QSpacerItem): name = 'spacer'
      else:                                  name = itm.widget().objectName()
      print i, name, gl.getItemPosition(i)

  def on_operation_changed(self, index):
  #-------------------------------------
    row = QtCore.QObject.sender(self).row
    lastrow = (row == len(self._rows) - 1)
    if index == 0 and not lastrow:
      for c in self._rows[row][:OPERATION]: c.hide()
      ##self._activerows -= 1     ## We now just label the row as "Ignored"
      c = self._rows[row][OPERATION]
      b = c.blockSignals(True)       # To stop ourselves being triggered...
      c.clear()                      # as we are changing the current operation
      c.addItem('Ignored')
      c.blockSignals(b)
    elif index > 0 and lastrow and row < (MAXROWS - 1):
      nextrow = [ ]
      next = len(self._rows)
      for n, c in enumerate(self._widgets[:VALUETEXT]):
        item = c.clone('%s%d' % (self._names[n], next), n in [PROPERTY, OPERATION])
        col = n if n < OPERATION else (n + 1)
        self.ui.gridLayout.addWidget(item, next, col)
        nextrow.append(item)
      self._rows[row][OPERATION].setItemText(0, 'Ignore')
      self._rows.append(nextrow)
      self._activerows += 1
      self.setup_last_row()
      self.ui.gridLayout.invalidate()
## This is if we want to resize containing widget...
#      height = 30*self._activerows
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
          values.hide()
          values = self._widgets[VALUE].clone('%s%d' % (self._names[VALUE], p.row))
          self._rows[p.row][VALUE] = values
          self.ui.gridLayout.addWidget(values, p.row, VALUE)
        values.addItem('Please select:')
        for v in valuelist: values.addItem(v)
      else:
        if not isinstance(values, LineEdit):
          values.hide()
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

  def as_XML(self):
  #----------------
    xml = [ ]
    for r in self._rows:
      prop = str(r[PROPERTY].currentText())
      if not prop.startswith('Please'):
        value = r[VALUE]
        if isinstance(value, ComboBox):
          text = str(value.currentText()) if value.currentIndex() > 0 else ''
        else:
          text = str(value.text()).strip()
### Need to XML escape property, relation, text
        if text and str(r[OPERATION].currentText()) != 'Ignored':
          xml.append('<term property=%s relation=%s>%s</term>'
                    % (quoteattr("%s" % prop),
                       quoteattr("%s" % r[RELATION].currentText()),
                       escape(text)))
          xml.append('<%s/>' % r[OPERATION].currentText().replace(' ', '_'))
    if xml: xml.pop()         # Remove last operator
    return ''.join(xml)

  @staticmethod
  def validate_XML(xml):
  #---------------------
    rows = 0
    operator = False
    for t in xml:
      if not operator:
        if t.tag != 'term': raise Exception, "Invalid search file"
        operator = True
        rows += 1
      else:
        if t.tag not in ['AND', 'AND_NOT', 'OR']:
          raise Exception, "Invalid term expression operator"
        operator = False
    if rows > MAXROWS:
      raise Exception, "Too many terms in saved search"
    if len(xml) > 0 and not operator:
      raise Exception, "Invalid saved search file"

  def _set_pulldown(self, value, row, col):
  #----------------------------------------
    if value:
      c = self._rows[row][col]
      i = c.findText(value)
      if i > 0:
        c.setCurrentIndex(i)  # Can trigger a signal --> slot

  def _set_value(self, value, row, col):
  #-------------------------------------
    if value:
      c = self._rows[row][col]
      if isinstance(c, ComboBox):
        self._set_pulldown(value, row, col)
      else:
        c.setText(value)

  def load_from_XML(self, xml):
  #----------------------------
    row = 0
    operator = False
    for t in xml:
      if not operator:
        self._set_pulldown(t.get('property'), row, PROPERTY)
        self._set_pulldown(t.get('relation'), row, RELATION)
        self._set_value(t.text, row, VALUE)
        operator = True
      else:
        self._set_pulldown(t.tag.replace('_', ' '), row, OPERATION)
        operator = False
        row += 1

  def remove_row(self, row):
  #-------------------------
    t = self._rows.pop(row)
    for c in t:
      i = self.ui.gridLayout.indexOf(c)
      c.hide()
      item = self.ui.gridLayout.itemAt(i)
      self.ui.gridLayout.removeItem(item)
      del c
      del item

  def clear_terms(self):
  #---------------------
    rows = len(self._rows)
    for row in xrange(1, rows):
      self.remove_row(row)
    c = self._rows[0][0]
    b = c.blockSignals(True)       # To stop ourselves being triggered...
    c.insertItem(0, 'Please select:')
    c.setCurrentIndex(0)
    c.show()                       # May have been hidden with ignore
    c.blockSignals(b)
    self._activerows = 1
    self.setup_last_row()
    self.ui.gridLayout.invalidate()
