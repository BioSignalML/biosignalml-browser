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
    self._metadata = None

    self._properties = sorted(['Text', 'Event', 'Duration', 'Recording', 'Database'])

    self._propvalues = {
      'Text': PropertyValue('text:stem',
                            sorted([ Relation('equal', 'text_match'),
                                     Relation('not equal', 'text_nomatch') ]),
                            'text'),
      'Event': PropertyValue('bsml:event',
                            sorted([ Relation('has type', 'uri_match'),
                                     Relation('not type', 'uri_nomatch') ]),
                            'list'),
      'Duration': PropertyValue('bsml:duration',
                            ['=', '!=', '<', '<=', '>', '>='],
                            'text'),
      'Recording': PropertyValue('bsml:recording',
                            sorted([ Relation('with URI',  'uri_match') ]),
                            'text'),
      'Database': PropertyValue('bsml:database',
                            sorted([ Relation('with URI',  'uri_match') ]),
                            'text'),
      }


  def properties(self):
  #--------------------
    return self._properties


  def relations(self, property):
  #-----------------------------
    pv = self._propvalues.get(str(property), None)
    if pv:
      if pv.relations and isinstance(pv.relations[0], tuple):
        return [ r.name for r in pv.relations ]
      else:
        return pv.relations
    return [ ]


  def values(self, property):
  #--------------------------
    pv = self._propvalues.get(str(property), None)
    if pv and pv.valuetype == 'list':
      values = [ ]
      for r in self._metadata.query("""select distinct ?value ?label where {
                                         [] <%s> ?value .
                                         optional { ?value rdfs:label ?label
                                         }""" % pv.uri,
                                     prefixes=prefixes):
        if r['label']: values.append(r['label'])
        else:          values.append(r['value'])
      return sorted(values)
    return ''

