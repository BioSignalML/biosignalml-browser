import sys
from PyQt4 import QtCore, QtGui

from query import Ui_QueryForm
from queryexpr import QueryExpr



class QueryForm(QtGui.QWidget):
#==============================

  def __init__(self, parent=None):
  #-------------------------------
    QtGui.QWidget.__init__(self, parent)
    self.ui = Ui_QueryForm()
    self.ui.setupUi(self)
    self.expressions = [ self.ui.expression ]
    self.expressions[0].hide_operation()
    #self.ui.chart.chartPosition.connect(self.on_chart_resize)
    #self.ui.time.valueChanged.connect(self.ui.chart.on_time_change)


  def new_expression(self):
  #------------------------
    expr = QueryExpr(self)
    self.expressions.append(expr)
    expr.terms[0].hide_operation()
    self.ui.verticalLayout.addWidget(expr)
    self.update()




if __name__ == "__main__":
#=========================
  app = QtGui.QApplication(sys.argv)
  query = QueryForm()
  query.show()
  sys.exit(app.exec_())
