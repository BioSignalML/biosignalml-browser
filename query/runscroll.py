import sys
from PyQt4 import QtCore, QtGui


from config import QueryConfig
from termgrid import TermGrid

from scroll import Ui_Form


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
    self._last_row = 0
    self.ui.operation.hide()
    self.add_operation(1)


  def add_operation(self, row):
  #----------------------------
    op = self.ui.operation.clone('operation%d' % row, True)
    op.row = row
    self.ui.gridLayout.addWidget(op, row, 1, QtCore.Qt.AlignTop)
    op.currentIndexChanged.connect(self.on_operation_changed)


  def on_operation_changed(self, index):
  #-------------------------------------
    op = QtCore.QObject.sender(self)
    if (index > 0
     and op.row == (self._last_row + 1)
     and str(op.itemText(0)).startswith('More')):
      item = self.ui.expression.clone('expression%d' % op.row)
      item.set_configuration(self.config)
      self.ui.gridLayout.addWidget(item, op.row, 2)
      op.removeItem(0)
      if op.row < 2: self.add_operation(op.row+1)
      self._last_row += 1



if __name__ == "__main__":
#=========================
  app = QtGui.QApplication(sys.argv)
  query = QueryForm(config=QueryConfig('config.ttl'))
  print query
  query.show()
  sys.exit(app.exec_())
