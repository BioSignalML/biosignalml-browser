import sys
import logging

from PyQt4 import QtCore, QtGui

from nrange import NumericRange
from tree import SortedResults

from ui.treeresults import Ui_Results


class Results(QtGui.QWidget):
#============================

  def __init__(self, repo_uri, results, parent=None):
  #--------------------------------------------------
    QtGui.QWidget.__init__(self, parent)

    self.results = Ui_Results()
    self.results.setupUi(self)
    self.setWindowTitle("Repository Browser")
    self.results.repository.setText(repo_uri)
    self.model = SortedResults(self.results.view, results, parent=self)


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
  
  query_results = [
    # Each row has [ reslabel, reslevel, resuri, type, prop, value ]
    [ 'db2',  1, 'db2', 'Database',  '',         ''   ],
    [ 'rec1', 2, 'rc1', 'Recording', 'duration', 1800 ],
    [ 'Signal', 3, 'r2/sg1', '',    'rdfs:label',    'V5' ],
    [ 'Signal', 3, 'sg2',    '',    'rdfs:label',    'V1' ],
    [ 'Event', 3, 'ev1', 'pvcBeat',  'count',         4   ],
    [ 'db',   1, 'db1', 'Database',  '',         ''   ],
    [ 'rec1', 2, 'rc1', 'Recording', 'duration', 1800 ],
    [ 'sig1', 3, 'sg1', 'Signal',    'label',    'V5' ],
    [ 'sig2', 3, 'sg2', 'Signal',    'label',    'V1' ],
    [ 'evt1', 3, 'ev1', 'Event',     'pvsBeat',   4   ],
    [ 'rec2', 2, 'rc2', 'Recording', 'duration', 1600 ],
   ]



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

  ## Following is a hack as QTreeView doesn't support word wrap....
  LINESIZE = 50

  def linesplit(l):
  #----------------
    words = l.split()
    lines = [ ]
    line = [ ]
    wordlen = 0
    for w in words:
      wordlen += len(w)
      line.append(w)
      if (wordlen + len(line) - 1) >= LINESIZE:
        lines.append(' '.join(line))
        line = [ ]
        wordlen = 0
    if line: lines.append(' '.join(line))
    return '\n'.join(lines)

  def seconds_to_hhmmss(secs):
  #---------------------------
    s = float(secs)
    hh = int(s)/3600
    mm = int(s)/60 % 60
    ss = s % 60
    return ('%d:%02d:0%g' if s < 10 else '%d:%02d:%g') % (hh, mm, ss)


  qr = rdfstore.select('?rec ?etype count(?etype) as ?count',
          """graph ?g {
               ?rec a bsml:Recording .
               ?res a bsml:Event ; bsml:eventType ?etype .
               }""",
          
          group='?rec ?etype',
          order='?rec ?etype',
          limit=400)    #### Need a paged view OFFSET xxx LIMIT yyy
  evts = [ [ abbreviate(str(v)) if isinstance(v, rdf.Uri) else v
                        for v in [ get_result_value(r, c) for c in 'rec etype count'.split() ] ]
                          for r in qr ]
  eventcounts = { }
  for r in evts:
    if r[0] not in eventcounts: eventcounts[r[0]] = [ ]
    eventcounts[r[0]].append(tuple(r[1:]))

  columns = 'db rec duration res rtype value'.split()
  where="""graph ?g {
                 ?rec a bsml:Recording ; dct:extent ?duration ; pbank:database ?db .
                 ?res a ?rtype .
                   { ?res a bsml:Signal ; bsml:recording ?rec ; rdfs:label ?value }
             union { ?res a bsml:Annotation ; rdfs:comment ?value }
                 }"""
  qr =  rdfstore.select(' '.join('?' + c for c in columns),
          where, limit=400,    #### Need a paged view OFFSET xxx LIMIT yyy
          order='?db ?rec ?res')
  rows = [ [ abbreviate(str(v)) if isinstance(v, rdf.Uri) else v
                        for v in [ get_result_value(r, c) for c in columns ] ]
                          for r in qr ]
  db = None
  rec = None
  repo = [ ]
  for r in rows:
    if r[0] != db:
      # Each row has [ reslabel, reslevel, resuri, type, prop, value ]
      repo.append([ r[0].rsplit('/', 1)[-1], 1, r[0], 'Database', '', '' ])
      db = r[0]
      rec = None
    if r[1] != rec:
      repo.append([ r[1].rsplit('/', 1)[-1], 2, r[1], 'Recording', 'duration', seconds_to_hhmmss(r[2]) ])
      rec = r[1]
      for evt in eventcounts.get(rec, []):
        repo.append([ 'Event', 3, evt[0], evt[0], 'count', evt[1] ])
    if r[4] == 'bsml:Signal':
      repo.append([ '/signal/' + r[3].rsplit('/', 1)[-1], 3, r[3], 'Signal', 'label', r[5] ])
    elif r[4] == 'bsml:Annotation':
      repo.append([ 'Annotation', 3, r[3], '', 'text', linesplit(r[5]) ])


  results = Results('http://demo.biosignalml.org/resources/physiobank', repo) # query_results)
  results.show()
  results.raise_()

  sys.exit(app.exec_())


"""
select distinct ?db ?rec ?duration ?res ?rtype ?value where {
  graph <http://devel.biosignalml.org/provenance> {
    ?g a bsml:RecordingGraph minus { [] prv:precededBy ?g }
    }
  graph ?g {
     ?rec a bsml:Recording ; dct:extent ?duration ; pbank:database ?db .
     { ?res a bsml:Signal ; bsml:recording ?rec ; rdfs:label ?value }
    union { ?res a bsml:Annotation ; rdfs:comment ?value }
    union { ?res a bsml:Event ; bsml:recording ?rec ; bsml:eventType ?value } .
   ?res a ?rtype
   }
  } 
order by ?db ?rec ?res


  """
