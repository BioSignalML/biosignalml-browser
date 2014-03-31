from PyQt5 import QtCore, QtWidgets


class SignalItem(QtWidgets.QStyledItemDelegate):
#===============================================

  def paint(self, painter, option, index):
  #---------------------------------------
    """
    Paint a centered checkbox in the first column of the table
    and draw a line underneath each table row,
    """
    r = option.rect
    viewoption = QtWidgets.QStyleOptionViewItem(option)
    if index.column() == 0:
      margin = QtWidgets.QApplication.style().pixelMetric(QtWidgets.QStyle.PM_FocusFrameHMargin) + 1
      viewoption.rect = QtWidgets.QStyle.alignedRect(option.direction, QtCore.Qt.AlignCenter,
                                                 QtCore.QSize(option.decorationSize.width() + 5, option.decorationSize.height()),
                                                 QtCore.QRect(r.x() + margin,
                                                              r.y(),
                                                              r.width() - (2 * margin),
                                                              r.height()))
    painter.drawLine(r.x(), r.y()+r.height(), r.x()+r.width(), r.y()+r.height())
    QtWidgets.QStyledItemDelegate.paint(self, painter, viewoption, index)

  def editorEvent(self, event, model, option, index):
  #--------------------------------------------------
    """
    Toggle checkbox on mouse click and key press.
    """
    flags = model.flags(index)
    if not (flags & (QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)):
      return False
    if not index.isValid(): return False
    value = index.data(QtCore.Qt.CheckStateRole)
    if not event.type() == QtCore.QEvent.MouseButtonRelease: return False
    margin = QtWidgets.QApplication.style().pixelMetric(QtWidgets.QStyle.PM_FocusFrameHMargin) + 1
    if not QtWidgets.QStyle.alignedRect(option.direction, QtCore.Qt.AlignCenter, option.decorationSize,
                                    QtCore.QRect(option.rect.x() + (2 * margin),
                                                 option.rect.y(),
                                                 option.rect.width() - (2 * margin),
                                                 option.rect.height())).contains(event.pos()): return False
    state = QtCore.Qt.Unchecked if (value == QtCore.Qt.Checked) else QtCore.Qt.Checked
    return model.setData(index, state, QtCore.Qt.CheckStateRole)


class SignalTable(QtWidgets.QTableView):
#=======================================

  rowSelected = QtCore.pyqtSignal(int)   # row, -1 means clear

  def __init__(self, *args, **kwds):
  #---------------------------------
    QtWidgets.QTableView.__init__(self, *args, **kwds)
    self.setItemDelegate(SignalItem(self))
    self.setShowGrid(False)
    self.verticalHeader().hide()
    self.horizontalHeader().setStretchLastSection(True)
    self.horizontalHeader().setHighlightSections(False)
    self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
    self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
    self._selectedrow = -1

  def mousePressEvent(self, event):
  #--------------------------------
    row = self.rowAt(event.pos().y())
    if row >= 0:
      self.selectRow(row)
      self._selectedrow = row
      self.rowSelected.emit(row)
    else:
      self.clearSelection()
      self.rowSelected.emit(-1)
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
    QtWidgets.QTableView.mouseReleaseEvent(self, event)
