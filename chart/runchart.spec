# -*- mode: python -*-
from PyInstaller.hooks.hookutils import collect_submodules

hiddenimports = []
hiddenimports.extend(collect_submodules('rdflib.plugins'))
hiddenimports.extend(collect_submodules('biosignalml'))

a = Analysis(['runchart.py'],
             pathex=['/Users/dave/biosignalml/browser/chart'],
             hiddenimports=hiddenimports,
             hookspath=['./hooks'],
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='runchart',
          debug=False,
          strip=None,
          upx=True,
          console=True )
