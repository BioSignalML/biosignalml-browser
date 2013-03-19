import urlparse
import threading
import Queue
import logging

from PyQt4 import QtCore, QtGui, QtWebKit

from biosignalml import client

from runchart import show_chart
from treemodel import TreeView, SortedUriTree


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


class QtBrowser(QtGui.QMainWindow):
#==================================

  def __init__(self, repo, recordings):
  #-------------------------
    super(QtBrowser, self).__init__()

#    toolmenu = QtGui.QMenu("File", self)
#    toolmenu.addAction(QtGui.QAction("Open", self, triggered=self.browse))
#    self.menuBar().addMenu(toolmenu)
#    self._repo = client.Repository(repo)
#    self.setWindowTitle(str(self._repo.uri))

    self.setWindowTitle(str(repo.uri))

#    recordings = [ ]
#    for uri in self._repo.recording_uris():
#      u = str(uri)
#      p = urlparse.urlparse(u)
#      recordings.append((tuple(p.path[1:].split('/')), u))

    tree = TreeView()
    self.model = SortedUriTree(tree, ['Path', 'Recording'], recordings, parent=self)
    self._viewers = [ ]
    tree.doubleClicked.connect(self.draw_chart)
    self.setCentralWidget(tree)


  def draw_chart(self, index):
  #--------------------------
    uri_index = index.sibling(index.row(), 1)
    if not uri_index.isValid(): return
    uri = str(uri_index.data().toString()).strip()
    if uri == '': return
    self._viewers.append(show_recording(uri))
    self._viewers[-1].show()


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

  app = QtGui.QApplication(sys.argv)

  recordings = recQ.get()
  rec_thread.join()

  if isinstance(recordings, str):
    sys.exit(recordings)

  browser = QtBrowser(repo, recordings)

  browser.show()
  browser.raise_()

  sys.exit(app.exec_())

