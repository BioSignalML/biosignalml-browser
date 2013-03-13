# -*- mode: python -*-
import sys

a = Analysis(['/Users/dave/biosignalml/browser/chart/QtBrowser.py'],
             pathex=['/Users/dave/build/pyinstaller-2.0'],
             hiddenimports=[],
             hookspath=None)

pyz = PYZ(a.pure - [
  ('matplotlib', '', ''),
  ('wx', '', ''),
  ])
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name=os.path.join('build/pyi.darwin/QtBrowser', 'QtBrowser'),
          debug=False,
          strip=None,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries - [
                 ('libwx_osx_cocoau-2.9.3.0.0.dylib', '', ''),
                 ('matplotlib._cntr', '', ''),
                 ('matplotlib._delaunay', '', ''),
                 ('matplotlib._image', '', ''),
                 ('matplotlib._path', '', ''),
                 ('matplotlib._png', '', ''),
                 ('matplotlib._tri', '', ''),
                 ('matplotlib.backends._backend_agg', '', ''),
                 ('matplotlib.backends._macosx', '', ''),
                 ('matplotlib.backends._tkagg', '', ''),
                 ('matplotlib.ft2font', '', ''),
                 ('matplotlib.nxutils', '', ''),
                 ('matplotlib.ttconv', '', ''),
                 ('wx._controls_', '', ''),
                 ('wx._core_', '', ''),
                 ('wx._gdi_', '', ''),
                 ('wx._misc_', '', ''),
                 ('wx._windows_', '', ''),
                 ],
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name=os.path.join('dist', 'QtBrowser'))
app = BUNDLE(coll,
             name=os.path.join('dist', 'QtBrowser.app'))
