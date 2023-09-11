all: chart.py annotate.py    \
     repo.py mainwindow.py signallist.py   \
     scroller.py annotationlist.py

%.py: %.ui
	pyuic6 $< -o $@
