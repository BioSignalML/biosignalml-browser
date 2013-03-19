from PyQt4 import QtCore, QtGui


class RowItem(object):
#=====================

  def __init__(self, name, parent):
  #-------------------------------
    self._name = name
    self._parent = parent
    self._children = [ ]
    self._names = { }
    self._data = None

  def add_item(self, name):
  #------------------------
    item = self._names.get(name)
    if item is None:
      item = RowItem(name, self)
      self._children.append(item)
      self._names[name] = item
    return item

  def set_data(self, data):
  #------------------------
    self._data = data

  def get_data(self, column):
  #--------------------------
    if column == 0: return self._name
    elif self._data is not None:
      try: return self._data[column-1]
      except IndexError: pass

  def branch(self):
  #----------------
    return len(self._children) > 0

  def parent(self):
  #----------------
    return self._parent

  def children(self):
  #------------------
    return len(self._children)

  def child(self, row):
  #--------------------
    return self._children[row]

  def columns(self):
  #-----------------
    return self.columns

  def row(self):
  #-------------
    if self._parent is not None:
      return self._parent._children.index(self)
    return 0



class UriTreeModel(QtCore.QAbstractItemModel):
#=============================================

  def __init__(self, hdr, details, parent=None):
  #---------------------------------------------
    super(UriTreeModel, self).__init__(parent)
    self._header = hdr
    self._root = RowItem('', None)
    for r in details:
      self._add_items(self._root, r[0], r[1:])

  def _add_items(self, node, path, data):
  #--------------------------------------
    item = node.add_item(path[0])
    if len(path) > 1:
      self._add_items(item, path[1:], data)
    else:
      item.set_data(data)


  def columnCount(self, parent):
  #-----------------------------
    return len(self._header)

  def data(self, index, role):
  #---------------------------
    if index.isValid():
      col = index.column()
      item = index.internalPointer()
      if   role == QtCore.Qt.DisplayRole:
        return item.get_data(col)
      elif role == QtCore.Qt.TextAlignmentRole:
        return QtCore.Qt.AlignTop
      elif col == 0 and role == QtCore.Qt.DecorationRole:
        if item.branch(): return QtGui.QApplication.style().standardIcon(QtGui.QStyle.SP_DirIcon)
        else:             return QtGui.QApplication.style().standardIcon(QtGui.QStyle.SP_FileIcon)
   ##   elif role == QtCore.Qt.ToolTipRole:
   ##     return item.get_data(1)  ## Could go to repo for metadata for tool-tip....
   ##     return '<div class="metadata"><p><span class="emphasised">Duration: </span><span class="details">0:13:45.389868</span></p><p><span class="emphasised">Format: </span><span class="details">application/x-bsml+hdf5</span></p><p><span class="emphasised">Imported: </span><span class="details">2013-03-11 02:28:30.602365+00:00</span></p><p><span class="emphasised">Importer: </span><span class="details">d.brooks@auckland.ac.nz</span></p></div>'
    return QtCore.QVariant()

  def flags(self, index):
  #----------------------
    if not index.isValid():
      return QtCore.Qt.NoItemFlags
    return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

  def headerData(self, section, orientation, role):
  #------------------------------------------------
    if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
      return self._header[section]
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
    return parentItem.children()



class SortedUriTree(QtGui.QSortFilterProxyModel):
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

  def __init__(self, view, hdr, details, parent=None):
  #---------------------------------------------------
    QtGui.QSortFilterProxyModel.__init__(self, parent)
    self._tree = UriTreeModel(hdr, details, parent)
    self.setSourceModel(self._tree)
    view.setModel(self)
    view.setSortingEnabled(True)
    self.sort(0, QtCore.Qt.AscendingOrder)
    view.header().setSortIndicator(0, QtCore.Qt.AscendingOrder)


class TreeView(QtGui.QTreeView):
#===============================

  def __init__(self, parent=None):
  #-------------------------------
    QtGui.QTreeView.__init__(self, parent)
    self.setAlternatingRowColors(True)
    self.setWordWrap(True)
    self.header().setStretchLastSection(True)
    self.header().setHighlightSections(False)
    self.header().setSortIndicatorShown(True)
    self.header().setResizeMode(QtGui.QHeaderView.ResizeToContents)
    self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
    self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)

