######################################################
#
#  BioSignalML Management in Python
#
#  Copyright (c) 2010-2012  David Brooks
#
######################################################


import Stemmer


class Sparql(object):
#====================

  def __init__(self, query):
  #-------------------------
    self.sparql = query

  @classmethod
  def create_from_XML(cls, xml):
  #------------------------------
    query = [ ]
    print xml ####
    return cls('\n'.join(query))


  def execute(self, rdfstore, format=None):  ## JSON, XML ??
  #----------------------------------------
    return None ## rdfstore.query(self.sparql, format)
