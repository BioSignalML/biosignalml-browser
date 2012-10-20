import sys
import logging

from PyQt4 import QtCore, QtGui

from table  import SortedTable
from nrange import NumericRange
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

  def resizeCells(self):
  #---------------------
    self.results.view.resizeCells()

  def resizeEvent(self, event):
  #----------------------------
    self.resizeCells()

  def showEvent(self, event):
  #--------------------------
    self.resizeCells()


if __name__ == "__main__":
#=========================

  import biosignalml.rdf as rdf
  from biosignalml.repository import BSMLStore
  from biosignalml.rdf.sparqlstore import Virtuoso
  from biosignalml.rdf.sparqlstore import get_result_value

  logging.basicConfig(format='%(asctime)s: %(message)s')
  logging.getLogger().setLevel('DEBUG')

  app = QtGui.QApplication(sys.argv)
  
  rdfstore = Virtuoso('http://localhost:8890')
  bsmlstore = BSMLStore('http://devel.biosignalml.org', rdfstore)

  PREFIXES = {
    'bsml': 'http://www.biosignalml.org/ontologies/2011/04/biosignalml#',
    'dct':  'http://purl.org/dc/terms/',
    'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
    'xsd':  'http://www.w3.org/2001/XMLSchema#',
    'pbank':	'http://www.biosignalml.org/ontologies/examples/physiobank#',

    'repo': 'http://devel.biosignalml.org/resource/',
    }

  def abbreviate(v):
  #-----------------
    for pfx, ns in PREFIXES.iteritems():
      if v.startswith(ns): return '%s:%s' % (pfx, v[len(ns):])
    return v

  rec_range = NumericRange(0, 1800)   #### Cludge ####

  summary = True

  if summary:
    header  = [ 'Recording', 'Resource', 'Property', 'Count', 'Value',  ]
    columns = [ 'rec',       'rtype',    'prop',     'ct',    'v',      ]
    count_query = """graph ?g {
                 ?rec a bsml:Recording .
                 ?res a ?rtype .
                 { ?res ?prop ?v . ?v bif:contains 'PVC or PVCs or "premature ventricular"' }
               union {
                 ?res ?prop ?v filter (?v = pbank:pvcBeat) .
                 }
               }"""
    grouping = '?rec ?rtype ?prop ?v'
    sparql_query = count_query
    query_cols = '?rec count(?v) as ?ct ?rtype ?prop ?v'
    query_order = '?rec ?v'

  else:
    header  = [ 'Recording', 'Resource', 'Offset (secs)', 'Property', 'Value' ]
    columns = [ 'rec',       'rtype',    'tm',            'prop',     'v',     ]
    time_query = """graph ?g {
                 ?rec a bsml:Recording .
                 ?res a ?rtype .
                 { ?res ?prop ?v . ?v bif:contains "PVC or PVCs" }
               union {
                 ?res ?prop ?v filter (?v = pbank:pvcBeat) .
                 }
               optional { ?res bsml:time ?time .
                 optional { ?time tl:at ?tm } .
                 optional { ?time tl:start ?tm } .
                 }
               }"""
    grouping = None
    sparql_query = time_query
    query_cols = ' '.join(('?' + c) for c in columns)
    query_order = '?rec ?res'


  qr =  rdfstore.select(query_cols,
          sparql_query,
          distinct=True,
          group=grouping,
          limit=100,    #### Need a paged view OFFSET xxx LIMIT yyy
          order=query_order)

  query_results = [ [ abbreviate(str(v)) if isinstance(v, rdf.Uri) else v
                        for v in [ get_result_value(r, c) for c in columns ] ]
                          for r in qr ]

  results = Results(header, query_results)
  results.show()
  results.raise_()

  sys.exit(app.exec_())


## ?res bsml:time ?tm . ?tm tl:duration "value"


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
