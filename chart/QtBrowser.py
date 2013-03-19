import urlparse

from PyQt4 import QtCore, QtGui

from biosignalml import client

from treemodel import TreeView, SortedUriTree


class QtBrowser(QtGui.QMainWindow):
#==================================

  def __init__(self, repo):
  #-------------------------
    super(QtBrowser, self).__init__()
    
#    toolmenu = QtGui.QMenu("File", self)
#    toolmenu.addAction(QtGui.QAction("Open", self, triggered=self.browse))
#    self.menuBar().addMenu(toolmenu)
    self._repo = client.Repository(repo)
    self.browse()

  def browse(self):
  #----------------
    recordings = [ ]
    for uri in self._repo.recording_uris():
      u = str(uri)
      p = urlparse.urlparse(u)
      recordings.append(((p.scheme + '://' + p.netloc,) + tuple(p.path[1:].split('/')), u))

    view = TreeView()
    self.model = SortedUriTree(view, ['Repository', 'Recording'], recordings, parent=self)
    self.setCentralWidget(view)


if __name__ == '__main__':
#=========================

  import sys

  if len(sys.argv) < 2:
    sys.exit("Usage: %s REPOSITORY" % sys.argv[0])

  app = QtGui.QApplication(sys.argv)
  browser = QtBrowser(sys.argv[1])
  browser.show()
  browser.raise_()

  sys.exit(app.exec_())


