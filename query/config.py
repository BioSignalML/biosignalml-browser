from collections import namedtuple

from biosignalml.rdf.sparqlstore import Virtuoso


PropertyValue = namedtuple('PropertyValue', ['uri', 'relations', 'valuetype'])

Relation      = namedtuple('Relation',      ['name', 'mapping'])


PREFIXES = {
  'bsml': 'http://www.biosignalml.org/ontologies/2011/04/biosignalml#',
  'dct':  'http://purl.org/dc/terms/',
  'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
  'pbank':	'http://www.biosignalml.org/ontologies/examples/physiobank#',

  'repo': 'http://devel.biosignalml.org/resource/',
  }

def abbreviate_uri(uri):
#=======================
  v = str(uri)
  for pfx, ns in PREFIXES.iteritems():
    if v.startswith(ns): return '%s:%s' % (pfx, v[len(ns):])
  return v


class QueryConfig(object):
#==========================

  def __init__(self, configuration):
  #---------------------------------
    """
    Reads and parses configuration information.

    Configuration includes location of RDF store.
    """

    self.rdfstore = Virtuoso('http://localhost:8890')

    self._propdata = {
      'Text': PropertyValue('bif:contains',
                            [ Relation('contains', 'text_word') ],
                            'text'),
      'Event': PropertyValue('bsml:eventType',
                            [ Relation('has type', 'uri_match'),
                              Relation('not type', 'uri_nomatch') ],
                            'list'),
      'Duration': PropertyValue('tl:duration',
                            ['=', '!=', '<', '<=', '>', '>='],
                            'text'),     ## Needs ?res bsml:time ?tm . ?tm tl:duration "value"
      'Recording': PropertyValue('bsml:recording',
                            [ Relation('with URI',  'uri_match') ],
                            'text'),
      'Database': PropertyValue('bsml:database',
                            [ Relation('with URI',  'uri_match') ],
                            'text'),
      }

    self._propvalues = { }
    for key, pv in self._propdata.iteritems():
      if pv.valuetype == 'list':
        values = [ ]
        for r in self.rdfstore.select('?value ?label',
                                      '[] %(uri)s ?value . optional { ?value rdfs:label ?label }',
                                      ## prefixes=prefixes,
                                      params=dict(uri=pv.uri)):
          if r['value'].get('label'): values.append(r['value']['label'])
          else:                       values.append(abbreviate_uri(r['value']['value']))
#        values = [ 'Normal beat', 'Fusion beat', 'Paced beat', 'PVC beat' ]  ###
        self._propvalues[key] = sorted(values)


  def properties(self):
  #--------------------
    return sorted(self._propdata)


  def relations(self, property):
  #-----------------------------
    pv = self._propdata.get(str(property), None)
    if pv:
      if pv.relations and isinstance(pv.relations[0], tuple):
        return sorted([ r.name for r in pv.relations ])
      else:
        return pv.relations
    return [ ]


  def values(self, property):
  #--------------------------
    return self._propvalues.get(str(property), '')
