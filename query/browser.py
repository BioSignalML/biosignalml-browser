import sys
import logging

from PyQt4 import QtCore, QtGui

from ui.results import Ui_Results


class ResultsTable(QtCore.QAbstractTableModel):
#==============================================

  def __init__(self, header, results, parent=None):
  #--------------------------------------------------
    QtCore.QAbstractTableModel.__init__(self, parent)
    self._header = header
    self._rows = results

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
        font = QtGui.QFont(QtGui.QApplication.font())
        font.setBold(True)
        return font

  def data(self, index, role):
  #---------------------------
    if   role == QtCore.Qt.DisplayRole:
      return str(self._rows[index.row()][index.column()])
    elif role == QtCore.Qt.TextAlignmentRole:
      return QtCore.Qt.AlignTop

  def flags(self, index):
  #-----------------------
    return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable


class Results(QtGui.QWidget):
#============================

  def __init__(self, header, results, parent=None):
  #------------------------------------------------
    QtGui.QWidget.__init__(self, parent)

    self.results = Ui_Results()
    self.results.setupUi(self)
    self.setWindowTitle("Query Results")

    self.model = ResultsTable(header, results, self)
    sorted = QtGui.QSortFilterProxyModel(self)
    sorted.setSourceModel(self.model)
    self.results.view.setModel(sorted)

  def resizeCells(self):  # Needs to be done after table is populated
  #---------------------
    selected = self.results.view.selectedIndexes()
    self.results.view.hide()
    self.results.view.resizeColumnsToContents()
    self.results.view.show()
    self.results.view.hide()
    self.results.view.resizeRowsToContents()
    if selected: self.results.view.selectRow(selected[0].row())
    self.results.view.show()


  def resizeEvent(self, event):
  #----------------------------
    self.resizeCells()


if __name__ == "__main__":
#=========================

  from biosignalml.rdf.sparqlstore import Virtuoso
  from biosignalml.repository import BSMLStore

  logging.basicConfig(format='%(asctime)s: %(message)s')
  logging.getLogger().setLevel('DEBUG')

  app = QtGui.QApplication(sys.argv)
  
  rdfstore = Virtuoso('http://localhost:8890')
  bsmlstore = BSMLStore('http://devel.biosignalml.org', rdfstore)

  PREFIXES = {
    'bsml': 'http://www.biosignalml.org/ontologies/2011/04/biosignalml#',
    'dct':  'http://purl.org/dc/terms/',
    'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
    'pbank':	'http://www.biosignalml.org/ontologies/examples/physiobank#',

    'repo': 'http://devel.biosignalml.org/resource/',
    }

  def abbreviate(v):
  #-----------------
    for pfx, ns in PREFIXES.iteritems():
      if v.startswith(ns): return '%s:%s' % (pfx, v[len(ns):])
    return v


  header  = [ 'Recording', 'Resource', 'Offset', 'Value' ]
  columns = [ 'rec',       'rtype',    'tm',     'v' ]

  NOVALUE = { 'value': '' }

  qr =  rdfstore.select(' '.join(('?' + c) for c in columns),
          """graph ?g {
               ?rec a bsml:Recording .
               ?res a ?rtype .
               { ?res ?p ?v . ?v bif:contains "PVC or PVCs" .
               }
               union
               { ?res bsml:eventType ?v filter (?v = pbank:pvcBeat) .
               }
             }""",
          distinct=True,
          order='?rec ?res')
  query_results = [ [ abbreviate(r.get(c, NOVALUE)['value']) for c in columns ] for r in qr ]

# [ 'Recording', 'has Resource', 'of Type', 'with Property', 'having a Value' ]

  results = Results(header, query_results)
  results.show()
  results.resizeCells()
  results.raise_()

  sys.exit(app.exec_())





  """
select distinct ?rec ?ct ?rtype ?v count(?v) as ?cv where {
  graph <http://devel.biosignalml.org/provenance> {
    ?g a bsml:RecordingGraph minus { [] prv:precededBy ?g }
    ?g prv:createdBy [ prv:completedAt ?ct ] .
    }
  graph ?g {
               ?rec a bsml:Recording .
               ?res a ?rtype .
               { ?res ?p ?v . ?v bif:contains "PVC or PVCs" }
               union
               { ?res bsml:eventType ?v filter (?v = pbank:pvcBeat) }
             }
  } group by ?rec ?ct ?rtype ?v
order by ?rec ?ct



select distinct ?rec ?ct ?rtype1 ?v1 ?rtype ?v where {
  graph <http://devel.biosignalml.org/provenance> {
    ?g a bsml:RecordingGraph minus { [] prv:precededBy ?g }
    ?g prv:createdBy [ prv:completedAt ?ct ] .
    }
  graph ?g {
               ?rec a bsml:Recording .
               ?res1 a ?rtype1 .
               { ?res1 ?p ?v1 . ?v1 bif:contains "PVC or PVCs" }
               ?res a ?rtype .
               { ?res bsml:eventType ?v filter (?v = pbank:pvcBeat) }
             }
  } 
order by ?rec ?ct

  """
