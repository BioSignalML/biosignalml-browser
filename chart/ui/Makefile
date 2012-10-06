all: chart.py controller.py annotate.py

%.py: %.ui
	pyuic4 $< -o $@
