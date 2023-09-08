"""
A generic widget and model for working with a tree view.

Selection by row and sortable columns are provided.
"""

from PyQt4 import QtCore, QtGui


## From PyQt-mac-gpl-4.9.4/examples/itemviews/simpletreemodel/simpletreemodel.py
##
#############################################################################
##
## Copyright (C) 2010 Riverbank Computing Limited.
## Copyright (C) 2010 Nokia Corporation and/or its subsidiary(-ies).
## All rights reserved.
##
## This file is part of the examples of PyQt.
##
## $QT_BEGIN_LICENSE:BSD$
## You may use this file under the terms of the BSD license as follows:
##
## "Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:
##   * Redistributions of source code must retain the above copyright
##     notice, this list of conditions and the following disclaimer.
##   * Redistributions in binary form must reproduce the above copyright
##     notice, this list of conditions and the following disclaimer in
##     the documentation and/or other materials provided with the
##     distribution.
##   * Neither the name of Nokia Corporation and its Subsidiary(-ies) nor
##     the names of its contributors may be used to endorse or promote
##     products derived from this software without specific prior written
##     permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
## $QT_END_LICENSE$
##
#############################################################################


class TreeItem(object):
#======================

  def __init__(self, data, parent=None):
    self.parentItem = parent
    self.itemData = data
    self.childItems = []

  def appendChild(self, item):
    self.childItems.append(item)

  def child(self, row):
    return self.childItems[row]

  def childCount(self):
    return len(self.childItems)

  def columnCount(self):
    return len(self.itemData)

  def data(self, column):
    try:
      return self.itemData[column]
    except IndexError:
      return None

  def parent(self):
    return self.parentItem

  def row(self):
    if self.parentItem:
      return self.parentItem.childItems.index(self)
    return 0



class ResultsTreeModel(QtCore.QAbstractItemModel):
#================================================

  def __init__(self, rows, parent=None):
  #-------------------------------------
    QtCore.QAbstractItemModel.__init__(self, parent)
    header = [ 'Resource', 'URI', 'Type', 'Property', 'Value' ]  ## With URI a hidden column
    self._root = TreeItem(header)
    # Each row has [ reslabel, reslevel, resuri, type, prop, value ]
    level = 0
    parents = [ self._root ]
    for r in rows:
      while level > r[1]:
        parents.pop()
        level -= 1
      if r[1] == level:
        item = TreeItem( r[0:1] + r[2:], parents[level-1] )
        parents[level-1].appendChild(item)
        parents[level] = item
      elif r[1] > level:
        item = TreeItem( r[0:1] + r[2:], parents[level] )
        parents[level].appendChild(item)
        parents.append(item)
        level = r[1]


  def columnCount(self, parent):
  #-----------------------------
    if parent.isValid():
      return parent.internalPointer().columnCount()
    else:
      return self._root.columnCount()

  def data(self, index, role):
  #---------------------------
    if index.isValid():
      col = index.column()
      item = index.internalPointer()
      if   role == QtCore.Qt.ItemDataRole.DisplayRole:
        return item.data(col)
      elif role == QtCore.Qt.ItemDataRole.TextAlignmentRole:
        return QtCore.Qt.AlignTop
      elif col == 0 and role == QtCore.Qt.ItemDataRole.DecorationRole:
        if item.data(2) == 'Database':
          return QtGui.QApplication.style().standardIcon(QtGui.QStyle.SP_DirIcon)
        elif item.data(2) == 'Recording':
          return QtGui.QApplication.style().standardIcon(QtGui.QStyle.SP_FileIcon)
      elif col == 0 and role == QtCore.Qt.ItemDataRole.ToolTipRole:
        return item.data(1)
    return QtCore.QVariant()

  def flags(self, index):
  #----------------------
    if not index.isValid():
      return QtCore.Qt.ItemFlag.NoItemFlags
    return QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable

  def headerData(self, section, orientation, role):
  #------------------------------------------------
    if orientation == QtCore.Qt.Orientation.Horizontal and role == QtCore.Qt.ItemDataRole.DisplayRole:
      return self._root.data(section)
    return None

  def index(self, row, column, parent):
  #------------------------------------
    if not self.hasIndex(row, column, parent):
      return QtCore.QModelIndex()
    if not parent.isValid():
      parentItem = self._root
    else:
      parentItem = parent.internalPointer()
    childItem = parentItem.child(row)
    if childItem:
      return self.createIndex(row, column, childItem)
    else:
      return QtCore.QModelIndex()

  def parent(self, index):
  #-----------------------
    if not index.isValid():
      return QtCore.QModelIndex()
    childItem = index.internalPointer()
    parentItem = childItem.parent()
    if parentItem == self._root:
      return QtCore.QModelIndex()
    return self.createIndex(parentItem.row(), 0, parentItem)

  def rowCount(self, parent):
  #--------------------------
    if parent.column() > 0:
      return 0
    if not parent.isValid():
      parentItem = self._root
    else:
      parentItem = parent.internalPointer()
    return parentItem.childCount()


#############################################################################


class SortedResults(QtGui.QSortFilterProxyModel):
#================================================
  """
  A generic sorted tree.

  :param view: A :class:`TreeView` in which the model is displayed.
  :param header (list): A list of column headings.
  :param rows (list): A list of tree data rows, with each element
     a list of the row's column data. The first column is used as
     a row identifier and is hidden.

  The initial view of the model is sorted on the second column (i.e. on
  the first visible column).
  """

  def __init__(self, view, rows, parent=None):
  #-------------------------------------------
    QtGui.QSortFilterProxyModel.__init__(self, parent)
    self._tree = ResultsTreeModel(rows, parent)
    self.setSourceModel(self._tree)
    view.setModel(self)
    view.setSortingEnabled(True)
    view.setColumnHidden(1, True)
    self.sort(0, QtCore.Qt.AscendingOrder)
    view.header().setSortIndicator(0, QtCore.Qt.AscendingOrder)



class TreeView(QtGui.QTreeView):
#===============================
  """
  A generic tree view.
  """

  def __init__(self, *args, **kwds):
  #---------------------------------
    QtGui.QTreeView.__init__(self, *args, **kwds)
    self.setAlternatingRowColors(True)
    self.setWordWrap(True)
    self.header().setStretchLastSection(True)
    self.header().setHighlightSections(False)
    self.header().setSortIndicatorShown(True)
    self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
    self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)

  def resizeCells(self):  # Needs to be done after tree is populated
  #---------------------  # But doesn't work.... ???
    selected = self.selectedIndexes()
    self.hide()
    self.setWordWrap(True)
    self.resizeColumnToContents(4)
    self.show()



