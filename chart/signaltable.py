from PyQt4 import QtCore, QtGui


class SignalItem(QtGui.QStyledItemDelegate):
#===========================================

  def paint(self, painter, option, index):
  #---------------------------------------
    """
    Paint a centered checkbox in the first column of the table
    and draw a line underneath each table row,
    """
    r = option.rect
    viewoption = QtGui.QStyleOptionViewItemV4(option)
    if index.column() == 0:
      margin = QtGui.QApplication.style().pixelMetric(QtGui.QStyle.PM_FocusFrameHMargin) + 1
      viewoption.rect = QtGui.QStyle.alignedRect(option.direction, QtCore.Qt.AlignCenter,
                                                 QtCore.QSize(option.decorationSize.width() + 5, option.decorationSize.height()),
                                                 QtCore.QRect(r.x() + margin,
                                                              r.y(),
                                                              r.width() - (2 * margin),
                                                              r.height()))
    painter.drawLine(r.x(), r.y()+r.height(), r.x()+r.width(), r.y()+r.height())
    QtGui.QStyledItemDelegate.paint(self, painter, viewoption, index)

  def editorEvent(self, event, model, option, index):
  #--------------------------------------------------
    """
    Toggle checkbox on mouse click and key press.
    """
    flags = model.flags(index)
    if not (flags & (QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)):
      return False
    value = index.data(QtCore.Qt.CheckStateRole)
    if not value.isValid(): return False
    if not event.type() == QtCore.QEvent.MouseButtonRelease: return False
    margin = QtGui.QApplication.style().pixelMetric(QtGui.QStyle.PM_FocusFrameHMargin) + 1
    if not QtGui.QStyle.alignedRect(option.direction, QtCore.Qt.AlignCenter, option.decorationSize,
                                    QtCore.QRect(option.rect.x() + (2 * margin),
                                                 option.rect.y(),
                                                 option.rect.width() - (2 * margin),
                                                 option.rect.height())).contains(event.pos()): return False
    state = QtCore.Qt.Unchecked if (value.toInt()[0] == QtCore.Qt.Checked) else QtCore.Qt.Checked
    return model.setData(index, state, QtCore.Qt.CheckStateRole)


class SignalTable(QtGui.QTableView):
#====================================

  def __init__(self, *args, **kwds):
  #---------------------------------
    QtGui.QTableView.__init__(self, *args, **kwds)
    self.setItemDelegate(SignalItem(self))
    self.setShowGrid(False)
    self.verticalHeader().hide()
    self.horizontalHeader().setStretchLastSection(True)
    self.horizontalHeader().setHighlightSections(False)
    self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
    self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
    self._selectedrow = -1

  def mousePressEvent(self, event):
  #--------------------------------
    row = self.rowAt(event.pos().y())
    if row >= 0:
      self.selectRow(row)
      self._selectedrow = row
    else:
      self.clearSelection()
    self.update()

  def mouseMoveEvent(self, event):
  #-------------------------------
    row = self.rowAt(event.pos().y())
    if self._selectedrow >= 0 and row >= 0 and self._selectedrow != row:
      dest = row if (row < self._selectedrow) else (row + 1)
      source = self._selectedrow
      model = self.model()
      index = QtCore.QModelIndex()
      if model.beginMoveRows(index, source , source, index, dest):
        model.moveRow(index, source, index, dest)
        model.endMoveRows()
        self._selectedrow = row
        self.selectRow(row)
        self.update()

  def mouseReleaseEvent(self, event):
  #----------------------------------
    self._selectedrow = -1
    QtGui.QTableView.mouseReleaseEvent(self, event)
