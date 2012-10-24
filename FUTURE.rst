Future Enhancments for QtBrowser
================================


 Update screen viewer picture with better time axis labelling (e.g. units);
 recording details; annotation; event bars; vertical zoom and scroll; signal
 selection; etc.

 Viewer control -- how much detail (turn on/off things like beat annotations
 (markers and/or text)); what signals are displayed and their order; what
 segment of a recording is shown; scroll/select/zoom; refresh v's live update...

 User control over presentation --- positioning of elements, colours, styles,
 themes, ...

 Simple query configuration


General
-------

* Provide a menubar for each module.

* Integrate modules into a single application.

* Add user authentication and record user as
  creator of new/edited annotations.

* Show recording and annotation provenance -- who
  created, when, ...

* Generate modules as executables (bbfreeze, py2app, pyinstaller
  (http://www.diotavelli.net/PyQtWiki/PyInstallerOnMacOSX), ... ??).

* Optionally show rdfs:label instead of URIs.

* Optionally abbreviate URIs (and specify base).

Chart Module
------------

* Allow existing annotations to be deleted via context menu.

  * This should require an "Are you sure?" confirmation.
  * Actual delete should be by creating an empty annotation
    whose predecessor is the one being deleted.
  * This would mean we then don't show (in controller's
    table) those annotations with no comment.
  * Or do we use some other property, including marking the
    latest version with a 'deleted' flag?
  * This is a more general issue and applies to deleting any
    resource, including recording graphs.

* Allow annotation history and older text to be viewed
  (including deleted annotations??).

* Use the same colour for annotation bars that have the same
  text (e.g. for beat annotations). We would need to also keep
  the annotation's text in '_annrects' and look it up as part
  of colour assignment.

* Allow deleted annotations to be "un-deleted"??
    
* Provide a control to adjust the viewer's total duration (in steps??).

* Provide a slider control to continuously adjust time zoom in viewer.

* Find data length/size of requested duration and either limit
  or alert user. (Best to tell user and limit as viewer becomes
  very slow...)

* Read data via streaming API (metadata still via direct connection
  to SparqlStore).

* Use REST API and/or web repository SPARQL endpoint for metadata.

* Show tooltip for event signal (instead of or as well as label
  in RHS from time marker ??).

* Show recording provenance.

* Allow supplementary details to be viewed (e.g. details of the
  recording's subject, etc). We could send HTML to a browser
  widget (and even allow links to be followed..!).

* Use modifier keys with mouse clicks??

* Change cursor depending on current operation (e.g. use a `hand`
  when moving selection region).

* Add option to display times as dThh:mm:ss, hh:mm:ss, mm:ss
  and also to use recording's start time if it exists.

* Show time position at mouse tip.


Query Module
------------
        
* Translate simple queries to SPARQL, perform the query,
  and show results using the results module.

  ::

    ?Sn a ?Tn ;
      <Pn> ?Vn filter (?Vn reln value) .

    ?Sn a ?Tn ; ?Pn ?On .
    ?On bif:contains "text" .

* Tidy up file names, remove earlier prototypes.

* Start the viewer from double-clicking a recording URI
  in the results view.

* Use subject of containing graph as the primary object returned
  by a search:::

    select distinct ?recording where {
      graph <provenance> {
        ?g a bsml:RecordingGraph minus { [] prv:preceededBy ?g } .
        ?g dct:subject ?recording
        }
      graph ?g {
        ?recording a bsml:Recording .
        # Search terms
        }
      }

* We could show query results in a text browser and allow links
  to be followed.


* General columns for search results:::

    | Recording | ResourceType | Resource | Value | SNORQL_Link |

* Abbreviate URIs where possible.

* If resource is an annotation then show its subject instead
  of the annotation URI.

* Use search view to display a recording graph's contents? Using
  a Qt TreeView? Can we paginate table? (c.f. SQL model ??).

* And allow user to hide/add/reorder columns??

* And use this as a general view of a repository/BSML Store??

* Then provenance graph could be another RDF graph displayed using
  this view.

* Live update giving user feedback during query and selection.

* Summaries of partial search results, classes of resources,
  categories of a given resource.


