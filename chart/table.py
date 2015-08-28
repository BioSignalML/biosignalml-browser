"""
A generic widget and model for working with a table view.

Selection by row and sortable columns are provided.
"""

from PyQt5 import QtCore, QtGui, QtWidgets


class TableView(QtWidgets.QTableView):
#=====================================
  """
  A generic table view.
  """

  def __init__(self, *args, **kwds):
  #---------------------------------
    QtWidgets.QTableView.__init__(self, *args, **kwds)
    self.setAlternatingRowColors(True)
    self.setShowGrid(False)
    self.setWordWrap(True)
    self.verticalHeader().setVisible(False)
    self.verticalHeader().sectionResizeMode(QtWidgets.QHeaderView.Fixed)
    self.verticalHeader().setDefaultSectionSize(18)
    self.horizontalHeader().setStretchLastSection(True)
    self.horizontalHeader().setHighlightSections(False)
    self.horizontalHeader().setSortIndicatorShown(True)
    self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
    self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

  def resizeCells(self):  # Needs to be done after table is populated
  #---------------------
    selected = self.selectedIndexes()
    self.hide()
    self.resizeColumnsToContents()
    self.show()
    self.hide()
    self.resizeRowsToContents()
    if selected: self.selectRow(selected[0].row())
    self.show()


class TableModel(QtCore.QAbstractTableModel):
#============================================
  """
  A generic table model.

  :param header (list): A list of column headings.
  :param rows (list): A list of table data rows, with each element
     a list of the row's column data. The first column is used as
     a row identifier and is normally hidden.
  """

  def __init__(self, header, rows, parent=None):
  #---------------------------------------------
    QtCore.QAbstractTableModel.__init__(self, parent)
    self._header = header
    self._rows = rows

    self._keys = { str(r[0]): n for n, r in enumerate(self._rows) }

  def rowCount(self, parent=None):
  #-------------------------------
    return len(self._rows)

  def columnCount(self, parent=None):
  #----------------------------------
    return len(self._header)

  def headerData(self, section, orientation, role):
  #------------------------------------------------
    if orientation == QtCore.Qt.Horizontal:
      if role == QtCore.Qt.DisplayRole:
        return self._header[section]
      elif role == QtCore.Qt.TextAlignmentRole:
        return QtCore.Qt.AlignLeft
      elif role == QtCore.Qt.FontRole:
        font = QtGui.QFont(QtWidgets.QApplication.font())
        font.setBold(True)
        return font

  def data(self, index, role):
  #---------------------------
    if   role == QtCore.Qt.DisplayRole:
      value = self._rows[index.row()][index.column()]
      return QtCore.QVariant(value) if value is not None else ''
    elif role == QtCore.Qt.TextAlignmentRole:
      return QtCore.Qt.AlignTop

  def flags(self, index):
  #-----------------------
    return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

  def appendRows(self, rows):
  #--------------------------
    posns = (len(self._rows), len(self._rows) + len(rows) - 1)
    self.beginInsertRows(self.createIndex(len(self._rows), 0), posns[0], posns[1])
    self._rows.extend(rows)
    self._keys = { str(r[0]): n for n, r in enumerate(self._rows) }
    self.endInsertRows()
    return posns

  def removeRows(self, posns):
  #---------------------------
    self.beginRemoveRows(self.createIndex(posns[0], 0), posns[0], posns[1])
    self._rows[posns[0]:posns[1]+1] = []
    self._keys = { str(r[0]): n for n, r in enumerate(self._rows) }
    self.endRemoveRows()

  def deleteRow(self, key):
  #------------------------
    n = self._keys.get(str(key), -1)
    if n >= 0: self.removeRows((n, n))


class SortedTable(QtCore.QSortFilterProxyModel):
#===============================================
  """
  A generic sorted table.

  :param view: A :class:`TableView` in which the model is displayed.
  :param header (list): A list of column headings.
  :param rows (list): A list of table data rows, with each element
     a list of the row's column data. The first column is used as
     a row identifier and is hidden.

  The initial view of the model is sorted on the second column (i.e. on
  the first visible column).
  """

  def __init__(self, view, header, rows, tablefilter=None, parent=None):
  #---------------------------------------------------------------------
    QtCore.QSortFilterProxyModel.__init__(self, parent)
    self._table = TableModel(header, rows, parent)
    self.setSourceModel(self._table)
    view.setModel(self)
    view.setSortingEnabled(True)
    view.setColumnHidden(0, True)
    self.sort(1, QtCore.Qt.AscendingOrder)
    view.horizontalHeader().setSortIndicator(1, QtCore.Qt.AscendingOrder)

#    self._filter = tablefilter    # function(row, content)
#
#  def setFilter(self, tablefilter):
#  #--------------------------------
#    self._table.layoutAboutToBeChanged.emit()
#    self._filter = tablefilter    # function(row, content)
#    self._table.layoutChanged.emit()
#
#  def clearFilter(self):
#  #---------------------
#    self._table.layoutAboutToBeChanged.emit()
#    self._filter = None
#    self._table.layoutChanged.emit()
#
#  def filterAcceptsRow(self, row, source):
#  #---------------------------------------
#    return (self._filter is None
#         or self._filter(row, self._table._rows[row]))

  def appendRows(self, rows):
  #--------------------------
    self._table.layoutAboutToBeChanged.emit()
    posns = self._table.appendRows(rows)
    self._table.layoutChanged.emit()
    return posns

  def removeRows(self, posns):
  #---------------------------
    self._table.layoutAboutToBeChanged.emit()
    self._table.removeRows(posns)
    self._table.layoutChanged.emit()

  def deleteRow(self, key):
  #------------------------
    self._table.layoutAboutToBeChanged.emit()
    self._table.deleteRow(key)
    self._table.layoutChanged.emit()

