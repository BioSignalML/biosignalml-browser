import sys
from PyQt4 import QtCore, QtGui

from scroll import Ui_Form
from termgrid import TermGrid


class QueryForm(QtGui.QWidget):
#==============================

  def __init__(self, parent=None):
  #-------------------------------
    QtGui.QWidget.__init__(self, parent)
    self.ui = Ui_Form()
    self.ui.setupUi(self)

    self.ui.Frame.setPalette(
      QtGui.QPalette(QtGui.QColor(200, 200, 255), QtGui.QColor(255, 255, 255))
      )

    self.ui.expression.row = 0
#    self.ui.expression.sizeChanged.connect(self.on_widget_resize)

    self._last_row = 0
    self.ui.operation.hide()
    self.add_operation(1)


  def on_widget_resize(self, height):
  #----------------------------------
    obj = QtCore.QObject.sender(self)
    row = obj.row
#    print obj.objectName(), row, height
#    if row == 0:
#      cell = self.ui.gridLayout.itemAtPosition(row, 0)
#      cell.changeSize(cell.sizeHint().width(), height)
    self.ui.gridLayout.invalidate()
    self.update()

  def add_operation(self, row):
  #----------------------------
    op = self.ui.operation.clone('operation%d' % row, True)
    op.row = row
    self.ui.gridLayout.addWidget(op, row, 1, QtCore.Qt.AlignTop)
    op.currentIndexChanged.connect(self.on_operation_changed)


  def on_operation_changed(self, index):
  #-------------------------------------
    row = QtCore.QObject.sender(self).row
    if index > 0 and row == (self._last_row + 1):
      item = self.ui.expression.clone('expression%d' % row)
      item.row = row
#      item.sizeChanged.connect(self.on_widget_resize)
      self.ui.gridLayout.addWidget(item, row, 2)
      QtCore.QObject.sender(self).removeItem(0)
      if row < 2: self.add_operation(row+1)
      self._last_row += 1



if __name__ == "__main__":
#=========================
  app = QtGui.QApplication(sys.argv)
  query = QueryForm()
  query.show()
  sys.exit(app.exec_())
