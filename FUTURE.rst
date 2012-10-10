Future Enhancments for QtBrowser
================================

General
-------

* Provide a menubar for each module.
* Integrate modules into a single application.


Chart Module
------------

* Allow existing annotations to be deleted via context menu.

  * This should require an "Are you sure?" confirmation.
  * Actual delete should be by creating an empty annotation
    whose predecessor is the one being deleted.
  * This would mean we then don't show (in controller's
    table) those annotations with no comment.
  * Or do we use some other property?
  * This is a more general issue and applies to deleting any
    resource, including recording graphs.
    
* Provide a control to adjust the viewer's duration.

* Find data length/size of requested duration and either limit
  or alert user. (Best to tell user and limit as viewer becomes
  very slow...)


Query Module
------------
        
* Translate simple queries to SPARQL, perform the query,
  and show results using the results module.
* Tidy up file names, remove earlier prototypes.
* Start the viewer from double-clicking a recording URI
  in the results view.
