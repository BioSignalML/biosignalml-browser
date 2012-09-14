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

    self.ui.gridLayoutWidget.setPalette(
      QtGui.QPalette(QtGui.QColor(200, 200, 255), QtGui.QColor(200, 255, 200))
      )
    self.ui.gridLayoutWidget.setAutoFillBackground(True)

    self.ui.expression.row = 0
    self.ui.expression.sizeChanged.connect(self.on_widget_resize)

    self.ui.operation.row = 1
    self.ui.operation.currentIndexChanged.connect(self.on_operation_changed)

    #self.expressions = [ self.ui.expression ]
    # operation  @ 1, 0
    # expression @ 0, 1


  def on_widget_resize(self, height):
  #----------------------------------
    row = QtCore.QObject.sender(self).row
    if row == 0:
      cell = self.ui.gridLayout.itemAtPosition(row, 0)
      cell.changeSize(cell.sizeHint().width(), height)
    self.ui.gridLayout.invalidate()
    self.update()

  def on_operation_changed(self, index):
  #------------------------
    op = QtCore.QObject.sender(self)
    row = op.row
    if index > 0:   # and row is last...
      
      item = self.ui.expression.clone('ex1')
      item.row = row
      item.sizeChanged.connect(self.on_widget_resize)
      self.ui.gridLayout.addWidget(item, row, 1)

##      self.ui.gridLayout.addItem(self.ui.gridLayout.itemAtLocation(row+1, 0), row+2, 0)
      newop = op.clone('nextop', True)
      newop.row = row + 1
      self.ui.gridLayout.addWidget(newop, row+1, 0)
      newop.currentIndexChanged.connect(self.on_operation_changed)



if __name__ == "__main__":
#=========================
  app = QtGui.QApplication(sys.argv)
  query = QueryForm()
  query.show()
  sys.exit(app.exec_())
