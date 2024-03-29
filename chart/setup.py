from setuptools import setup

import shutil
shutil.rmtree("build", ignore_errors=True)
shutil.rmtree("dist", ignore_errors=True)

APPNAME = 'QtBrowser'
APP = ['runchart.py']
VERSION = '0.5.0a'

DATA_FILES = []
## DATA_FILES = ['gpl-3.0.txt']

OPTIONS = {'argv_emulation': False,
           'compressed': True,
           'packages': ['pint'],
           'includes': ['PyQt6'], ##, 'pint.*'],
           'excludes': ['modulegraph', 'graph_tool', 'sympy', 'scipy',
                        'wx', 'matplotlib', 'OpenGL', 'zmq'],
           'dylib_excludes': ['Tcl.framework','Tk.framework'],
          }

setup(
app=APP,
data_files=DATA_FILES,
options={'py2app': OPTIONS},
setup_requires=['py2app'],
)

