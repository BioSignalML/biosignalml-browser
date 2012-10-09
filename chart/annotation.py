from PyQt4 import QtCore, QtGui

from ui.annotate import Ui_AnnotationDialog


class Annotation(QtGui.QDialog):
#===============================

  def __init__(self, start, end, parent=None):
  #-------------------------------------------
    QtGui.QDialog.__init__(self, parent)
    self.ui = Ui_AnnotationDialog()
    self.ui.setupUi(self)

  def annotation(self):
  #--------------------
    return self.ui.annotation.toPlainText()

  def setAnnotation(self, text):
  #-----------------------------
    self.ui.annotation.setPlainText(text)

