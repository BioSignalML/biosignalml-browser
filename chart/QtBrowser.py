import logging
import os, sys

## This is so we can import pint when running via py2exe
if hasattr(sys,"frozen") and len(sys.path) == 1:
  libpath = os.path.dirname(sys.path[0])
  sys.path.insert(0, libpath)
  sys.path_importer_cache[libpath] = None
##

from PyQt4 import QtCore, QtGui, QtWebKit

from biosignalml import client
from biosignalml.rdf.sparqlstore import StoreException

from runchart import show_chart
from ui.repo import Ui_SelectRepository


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
    closekey = QtGui.QShortcut(QtGui.QKeySequence.Close, self, activated=self.close)
    refresh = QtGui.QShortcut(QtGui.QKeySequence.Refresh, self, activated=self.reload)
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
    except StoreException, msg:
      alert = QtGui.QMessageBox()
      alert.setText(str(msg))
      alert.exec_()
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
          chart.viewer.activateWindow()

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


class RepositoryDialog(QtGui.QDialog):
#=====================================

  def __init__(self, repo, parent=None):
  #-------------------------------------
    QtGui.QWidget.__init__(self, parent)
    closekey = QtGui.QShortcut(QtGui.QKeySequence.Close, self, activated=self.close)
    self.input = Ui_SelectRepository()
    self.input.setupUi(self)
    self.input.repository.addItem("")
    repos = client.Repository.known_repositories()
    if repo != '' and repo not in repos: repos.append(repo)
    self.input.repository.addItems(sorted(repos))
    self.input.repository.setCurrentIndex(self.input.repository.findText(repo))


if __name__ == '__main__':
#=========================

#  logging.basicConfig(format='%(asctime)s %(levelname)8s %(threadName)s: %(message)s')
#  logging.getLogger().setLevel('DEBUG')

  app = QtGui.QApplication(sys.argv)

  settings = QtCore.QSettings('biosignalml.org', 'QtBrowser')

  dialog = RepositoryDialog(settings.value('repository', '').toString())
  dialog.show()
  dialog.raise_()
  while dialog.exec_():
    input = dialog.input
    url = QtCore.QUrl.fromUserInput(input.repository.currentText())
    if url.isValid():
      url = str(url.toString())
      try:
        repo = client.Repository(url, str(input.username.text()), str(input.password.text()))
        if repo.access_token is None:
          raise IOError("Invalid username/password")
        # Better to first check client.Repository.authenticated(url)
        # and if not get name/password and:
        #   repo = client.Repository(url, name, password)
        # This process will add repo to list of known ones.

        settings.setValue('repository', url)
        browser = WebBrowser(url)
        app.exec_()
      except IOError, msg:
        alert = QtGui.QMessageBox()
        alert.setText("Cannot connect to repository: %s" % msg)
        alert.exec_()





