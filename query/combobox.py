from PyQt4 import QtCore, QtGui


class ComboBox(QtGui.QComboBox):
#===============================

  def clone(self, name, copyItems=False):
  #--------------------------------------
    copy = self.__class__(self.parentWidget())
    copy.setSizePolicy(self.sizePolicy())
    copy.setMinimumSize(self.minimumSize())
    copy.setMaximumSize(self.maximumSize())
    copy.setObjectName(name)
    if copyItems:
      for i in xrange(self.count()):
        copy.addItem(self.itemIcon(i), self.itemText(i))
    return copy
