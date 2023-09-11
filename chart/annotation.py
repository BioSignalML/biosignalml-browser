#===============================================================================

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import pyqtSignal, pyqtSlot

#===============================================================================

from ui.annotate import Ui_AnnotationDialog

#===============================================================================

class TagItem(QtWidgets.QListWidgetItem):
#========================================

  def __init__(self, uri, label):
  #------------------------------
    QtWidgets.QListWidgetItem.__init__(self, label)
    self.uri = uri
    self.label = label

#===============================================================================

class AnnotationDialog(QtWidgets.QDialog):
#=========================================

  def __init__(self, id, start, end, text='', tags=None, parent=None):
  #-------------------------------------------------------------------
    QtWidgets.QDialog.__init__(self, parent)
    self.ui = Ui_AnnotationDialog()
    self.ui.setupUi(self)
    if id.startswith('http://'):
      p = id[7:].split('/')
      if len(p) > 1: id = '/'.join(p[1:])
    self.setWindowTitle(id)
    self.ui.description.setText('Annotate %g to %g seconds' % (start, end))
    self.ui.annotation.setPlainText(text)

    if tags is None: tags = [ ]
    semantic_tags = parent.semantic_tags  # { uri: label }
    self.ui.taglist.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
    for u, l in semantic_tags.items(): self.ui.taglist.addItem(TagItem(u, l))
    for t in tags:   ## Show 'unknown' tags
      if t not in semantic_tags: self.ui.taglist.addItem(TagItem(t, str(t)))
    self.ui.taglist.sortItems()
    ## Setting selected as items are added doesn't work (because of sort??)
    for n in range(self.ui.taglist.count()):
      t = self.ui.taglist.item(n)
      if t.uri in tags: t.setSelected(True)
    self.ui.taglist.hide()
    self._tags_visible = False
    self.ui.tags.clicked.connect(self.show_tags)
    self.ui.taglabels.setText(', '.join(sorted([semantic_tags.get(t, str(t)) for t in tags])))

  def get_annotation(self):
  #------------------------
    return str(self.ui.annotation.toPlainText()).strip()

  @pyqtSlot()
  def show_tags(self):
  #-------------------
    self.ui.taglabels.setText(', '.join(sorted([t.label for t in self.ui.taglist.selectedItems()])))
    self._tags_visible = not self._tags_visible
    self.ui.taglist.setVisible(self._tags_visible)

  def get_tags(self):
  #------------------
     return [ t.uri for t in self.ui.taglist.selectedItems() ]

#===============================================================================
