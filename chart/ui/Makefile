all: chart.py controller.py annotate.py    \
     repo.py mainwindow.py signallist.py   \
     scroller.py annotationlist.py

%.py: %.ui
	pyuic5 $< -o $@
