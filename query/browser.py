import sys
import logging

from PyQt4 import QtCore, QtGui

from table import SortedTable
##from tree import SortedTree

from ui.results import Ui_Results
##from ui.treeresults import Ui_Results


class Results(QtGui.QWidget):
#============================

  def __init__(self, header, results, parent=None):
  #------------------------------------------------
    QtGui.QWidget.__init__(self, parent)

    self.results = Ui_Results()
    self.results.setupUi(self)
    self.setWindowTitle("Query Results")
    self.model = SortedTable(self.results.view,
                             [''] + header, [[n] + r for n, r in enumerate(results)],
                             parent=self)

  def resizeEvent(self, event):
  #----------------------------
    self.resizeCells()

  def resizeCells(self):
  #---------------------
    self.results.view.resizeCells()


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
