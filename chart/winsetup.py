from distutils.core import setup
import py2exe

import numpy


import shutil
shutil.rmtree("build", ignore_errors=True)
shutil.rmtree("dist", ignore_errors=True)

APPNAME = 'QtBrowser'
APP = ['QtBrowser.py']
VERSION = '0.4.1'

PINT = 'C:\\Python27\\Lib\\site-packages\\pint-0.1.3_djb-py2.7.egg\\pint\\'

DATA_FILES = [ ('pint', [PINT + '__init__.py', PINT + 'pint.py', PINT + 'default_en.txt']) ]

## DATA_FILES = ['gpl-3.0.txt']

OPTIONS = {
           'compressed': True,
           'optimize': 2,
           'bundle_files': 1,
           'includes': ['PyQt4', 'PyQt4.QtNetwork', 'sip'],
           'packages': ['pint'],
           'excludes': ['modulegraph', 'graph_tool', 'sympy', 'scipy',
                        'wx', 'matplotlib', 'OpenGL', 'zmq',
                        'numpy.core._dotblas',
                        'numpy.f2py',
                        'numpy.distutils',
                        'pydoc',
                        'pydoc_data',
                        'compiler',
                        'distutils',
                        'setuptools',
                       ]

          }

setup(
  windows=APP,
  zipfile=None,
  data_files=DATA_FILES,
  options={'py2exe': OPTIONS},
##    icon_resources = [(1, "icon.ico")],
  )

