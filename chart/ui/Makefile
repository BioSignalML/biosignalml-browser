all: chart.py controller.py annotate.py repo.py

%.py: %.ui
	pyuic5 $< -o $@
