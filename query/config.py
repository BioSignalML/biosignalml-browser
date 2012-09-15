from collections import namedtuple


PropertyValue = namedtuple('PropertyValue', ['uri', 'relations', 'valuetype'])

Relation      = namedtuple('Relation',      ['name', 'mapping'])



class QueryConfig(object):
#==========================

  def __init__(self, configuration):
  #---------------------------------
    """
    Reads and parses configuration information.

    Configuration includes location of RDF store.
    """

    metadata = None

    self._propdata = {
      'Text': PropertyValue('text:stem',
                            [ Relation('has word', 'text_word'),
                              Relation('no word',  'text_noword') ],
                            'text'),
      'Event': PropertyValue('bsml:event',
                            [ Relation('has type', 'uri_match'),
                              Relation('not type', 'uri_nomatch') ],
                            'list'),
      'Duration': PropertyValue('bsml:duration',
                            ['=', '!=', '<', '<=', '>', '>='],
                            'text'),
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
#        for r in metadata.query("""select distinct ?value ?label where {
#                                     [] <%s> ?value .
#                                     optional { ?value rdfs:label ?label
#                                     }""" % pv.uri,
#                                 prefixes=prefixes):
#          if r['label']: values.append(r['label'])
#          else:          values.append(r['value'])
        values = [ 'Normal beat', 'Fusion beat', 'Paced beat', 'PVC beat' ]  ###
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
