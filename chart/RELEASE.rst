::

  rm -rf dist build
  python setup.py py2app
  hdiutil create -imagekey zlib-level=9 -srcfolder dist/QtBrowser.app dist/QtBrowser.dmg
