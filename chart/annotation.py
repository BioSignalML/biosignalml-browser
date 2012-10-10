from PyQt4 import QtCore, QtGui

from ui.annotate import Ui_AnnotationDialog


class AnnotationDialog(QtGui.QDialog):
#=====================================

  def __init__(self, id, start, end, text='', parent=None):
  #--------------------------------------------------------
    QtGui.QDialog.__init__(self, parent)
    self.ui = Ui_AnnotationDialog()
    self.ui.setupUi(self)
    if id.startswith('http://'):
      p = id[7:].split('/')
      if len(p) > 1: id = '/'.join(p[1:])
    self.setWindowTitle(id)
    self.ui.description.setText('Annotate %g to %g seconds' % (start, end))
    self.ui.annotation.setPlainText(text)

  def annotation(self):
  #--------------------
    return self.ui.annotation.toPlainText()
