import urlparse
import threading
import Queue
import logging

from PyQt4 import QtCore, QtGui, QtWebKit

from biosignalml import client

from treemodel import TreeView, SortedUriTree
from runchart import show_chart


class RepoRecordings(threading.Thread):
#======================================

  def __init__(self, repo, recQ):
  #------------------
    threading.Thread.__init__(self)
    self._repo = repo
    self._recQ = recQ
    self.start()

  def run(self):
  #-------------
    recordings = [ ]
    try:
      for uri in self._repo.recording_uris():
        u = str(uri)
        p = urlparse.urlparse(u)
        recordings.append((tuple(p.path[1:].split('/')), u))
      self._recQ.put(recordings)
    except Exception, msg:
      self._recQ.put(str(msg))


#class QtBrowser(QtGui.QMainWindow):
##==================================
#
#  def __init__(self, repo, recordings):
#  #-------------------------
#    super(QtBrowser, self).__init__()
#
##    toolmenu = QtGui.QMenu("File", self)
##    toolmenu.addAction(QtGui.QAction("Open", self, triggered=self.browse))
##    self.menuBar().addMenu(toolmenu)
##    self._repo = client.Repository(repo)
##    self.setWindowTitle(str(self._repo.uri))
#
#    self.setWindowTitle(str(repo.uri))
#
##    recordings = [ ]
##    for uri in self._repo.recording_uris():
##      u = str(uri)
##      p = urlparse.urlparse(u)
##      recordings.append((tuple(p.path[1:].split('/')), u))
#
#    tree = TreeView()
#    self.model = SortedUriTree(tree, ['Path', 'Recording'], recordings, parent=self)
#    self._viewers = [ ]
#    tree.doubleClicked.connect(self.draw_chart)
#    self.setCentralWidget(tree)
#
#
#  def draw_chart(self, index):
#  #--------------------------
#    uri_index = index.sibling(index.row(), 1)
#    if not uri_index.isValid(): return
#    uri = str(uri_index.data().toString()).strip()
#    if uri == '': return
#    self._viewers.append(show_recording(uri))
#    self._viewers[-1].show()




class WebPage(QtWebKit.QWebPage):
#================================

  def __init__(self, parent=None):
  #-------------------------------
    super(WebPage, self).__init__(parent)
#    self.setLinkDelegationPolicy(QtWebKit.QWebPage.DelegateAllLinks)
#    self.linkHovered.connect(self.link_hovered)
#    self.linkClicked.connect(self.link_clicked)

  def triggerAction(self, action, checked=False):
  #----------------------------------------------
    if action == QtWebKit.QWebPage.OpenLinkInNewWindow:
      self.createWindow(QtWebKit.QWebPage.WebBrowserWindow)
    return super(WebPage, self).triggerAction(action, checked)

#  def link_hovered(self, link, title, content):
#  #--------------------------------------------
#    logging.debug("Hovering... %s, %s, %s", link, title, content)

#  def link_clicked(self, url):
#  #---------------------------
#    print "Clicked...", url, url.path()
#    self.view().load(url)


class WebView(QtWebKit.QWebView):
#================================

  def __init__(self, repo, parent=None):
  #-------------------------------------
    super(WebView, self).__init__(parent)
    self.setPage(WebPage(self))
    self._charts = [ ]
    if repo is not None:
      self.load(QtCore.QUrl(repo))
      self.show()
      self.raise_()

  def contextMenuEvent(self, event):
  #---------------------------------
    pos = event.pos()
    element = self.page().mainFrame().hitTestContent(pos)
    link_url = str(element.linkUrl().toString())
    print link_url, element.linkTargetFrame()
    ## element.linkTargetFrame() == None when <a> target is blank...
    menu = self.page().createStandardContextMenu()
    menu.addSeparator()
    menu.addAction(self.pageAction(QtWebKit.QWebPage.Back))
    menu.addAction(self.pageAction(QtWebKit.QWebPage.Forward))
    menu.addAction(self.pageAction(QtWebKit.QWebPage.Reload))
    try:  ## Check if link_url refers to a recording...
      store = client.Repository(link_url)
      recording = store.get_recording(link_url)
      menu.addSeparator()
      action = menu.addAction('View Recording')
    except IOError:
      pass
    item = menu.exec_(self.mapToGlobal(pos))
    if item:
      if item.text() == 'View Recording':
        chart = show_chart(store, recording)
        if chart is not None:
          self._charts.append(chart)
          chart.show()
          chart.viewer.raise_()

  def createWindow(self, type):
  #----------------------------
    if type == QtWebKit.QWebPage.WebBrowserWindow:
      # print "Creating window...", type, self.url()
      self._view = WebView(None)
      self._view.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
      return self._view
    return super(WebView, self).createWindow(type)


class WebBrowser(QtGui.QMainWindow):
#==================================

  def __init__(self, repo):
  #------------------------
    super(WebBrowser, self).__init__()
    self._view = WebView(repo)



if __name__ == '__main__':
#=========================

  import sys
#  if len(sys.argv) < 2:
#    sys.exit("Usage: %s REPOSITORY" % sys.argv[0])

#  logging.basicConfig(format='%(asctime)s %(levelname)8s %(threadName)s: %(message)s')
#  logging.getLogger().setLevel('DEBUG')
  #repo_url = 'http://devel.biosignalml.org' # sys.argv[1]
  try:
    repo_url = sys.argv[1]
    repo = client.Repository(repo_url)
  except IOError:
    sys.exit("Cannot connect to repository")
  recQ = Queue.Queue()
  rec_thread = RepoRecordings(repo, recQ)

  #app = QtGui.QApplication(['QtBrowser']) # sys.argv)
  app = QtGui.QApplication(sys.argv)
#  browser = QtBrowser(sys.argv[1])
  browser = WebBrowser(repo_url)

#  recordings = recQ.get()
#  rec_thread.join()
#
#  if isinstance(recordings, str):
#    sys.exit(recordings)
#
#  browser = QtBrowser(repo, recordings)

#  browser.show()
#  browser.raise_()

  sys.exit(app.exec_())


