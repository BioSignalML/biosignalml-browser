import sys
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

from PyQt4 import QtCore, QtGui


from config import QueryConfig
from termgrid import TermGrid
from sparql import Sparql

from scroll import Ui_Form


MAXROWS = 3   #: Maximum number of term expressions


class QueryForm(QtGui.QWidget):
#==============================

  def __init__(self, parent=None, config=None):
  #--------------------------------------------
    QtGui.QWidget.__init__(self, parent)
    self.ui = Ui_Form()
    self.ui.setupUi(self)
    self.ui.Frame.setPalette(
      QtGui.QPalette(QtGui.QColor(200, 200, 255), QtGui.QColor(255, 255, 255))
      )
    self.config = config
    self.ui.expression.set_configuration(config)
    self._rows = [ [ self.ui.operation, self.ui.expression ] ]
    self._lastrow = 0
    self.ui.operation.hide()
    self.add_operation(1)

  def add_operation(self, row):
  #----------------------------
    op = self.ui.operation.clone('operation%d' % row, True)
    op.row = row
    self.ui.gridLayout.addWidget(op, row, 1, QtCore.Qt.AlignTop)
    op.currentIndexChanged.connect(self.on_operation_changed)
    self._rows.append([ op, None ])

  def on_operation_changed(self, index):
  #-------------------------------------
    op = QtCore.QObject.sender(self)
    if (index > 0
     and op.row == (self._lastrow + 1)
     and str(op.itemText(0)).startswith('More')):
      item = self.ui.expression.clone('expression%d' % op.row)
      item.set_configuration(self.config)
      self.ui.gridLayout.addWidget(item, op.row, 2)
      self._rows[op.row][1] = item
      op.removeItem(0)
      if op.row < (MAXROWS - 1): self.add_operation(op.row+1)
      self._lastrow += 1

  def on_search_released(self):  # Auto connected
  #----------------------------
    query = Sparql.create_from_XML(self.as_XML())
    results = query.execute(self.config.rdfstore)

  def on_clear_released(self):   # Auto connected
  #---------------------------
    self.clear_form()

  def on_save_released(self):    # Auto connected
  #-------------------------
    filename = QtGui.QFileDialog.getSaveFileName(self, 'Save search', '', '*.xml')
    if filename:
      f = open(filename, 'w')
      f.write(self.as_XML())
      f.close()

  def on_load_released(self):    # Auto connected
  #-------------------------
    filename = QtGui.QFileDialog.getOpenFileName(self, 'Load search', '', '*.xml')
    if not filename: return
    try:
      root = ET.parse(filename)
      self.validate_XML(root)
      self.load_from_XML(root)
    except Exception, msg:
      alert = QtGui.QMessageBox()
      alert.setText(str(msg))
      alert.exec_()

  def as_XML(self):
  #----------------
    xml = [ ]
    xml.append('<query>')
    desc = str(self.ui.description.toPlainText())
    if desc:
      xml.append('<description>')
      xml.append(escape(desc))
      xml.append('</description>')
    firstop = len(xml)
    for n, e in enumerate(self._rows):
      if e[1]:
        t = e[1].as_XML()
        if t:
          xml.append(' <%s/>' % str(e[0].currentText()).replace(' ', '_'))
          xml.append(' <expr>')
          xml.append('  %s' % t)
          xml.append(' </expr>')
    if len(xml) > firstop: xml.pop(firstop)  # Remove operator before first expression
    xml.append('</query>')
    return '\n'.join(xml)

  def validate_XML(self, xml):
  #---------------------------
    if xml.getroot().tag != 'query': raise Exception, "Not a saved search file"
    rows = 0
    operator = False
    for e in xml.findall('*'):
      if e.tag == 'description':
        pass
      elif not operator:
        if e.tag != 'expr': raise Exception, "Invalid saved search file"
        TermGrid.validate_XML(e.findall('*'))
        operator = True
        rows += 1
      else:
        if e.tag not in ['AND', 'AND_NOT', 'OR']:
          raise Exception, "Invalid expression operator"
        operator = False
    if rows > MAXROWS:
      raise Exception, "Too many term expressions in saved search"
    if len(e) > 0 and not operator:
      raise Exception, "Invalid saved search file"

  def _set_pulldown(self, value, row, col):
  #----------------------------------------
    if value:
      c = self._rows[row][col]
      i = c.findText(value)
      if i > 0:
        c.setCurrentIndex(i)  # Can trigger a signal --> slot

  def load_from_XML(self, xml):
  #----------------------------
    self.clear_form()
    row = 0
    operator = False
    for e in xml.findall('*'):
      if e.tag == 'description':
        self.ui.description.setPlainText(e.text.strip())
      elif not operator:
        self._rows[row][1].load_from_XML(e.findall('*'))
        operator = True
        row += 1           # Check not too many...
      else:
        self._set_pulldown(e.tag.replace('_', ' '), row, 0)
        operator = False

  def clear_form(self):
  #---------------------
    self.ui.description.clear()
    for n in xrange(len(self._rows) - 1):
      e = self._rows.pop()
      for m, c in enumerate(e):
        if c:
          c.hide()
          item = self.ui.gridLayout.itemAtPosition(n+1, m)
          self.ui.gridLayout.removeItem(item)
          del c
          del item
    self._rows[0][1].clear_terms()
    self._lastrow = 0
    self.add_operation(1)


if __name__ == "__main__":
#=========================
  app = QtGui.QApplication(sys.argv)
  query = QueryForm(config=QueryConfig('config.ttl'))
  query.ui.cancel.released.connect(app.quit)
  query.show()
  query.raise_()
  sys.exit(app.exec_())
