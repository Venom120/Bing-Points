.PHONY: run install uninstall

run:
	@echo off
	python -m venv .venv
	source .venv/bin/activate && pip install -r req.txt
	@echo on
	python main.py

install:
	python -m venv .venv
	source .venv/bin/activate && pip install -r req.txt
	mkdir /usr/share/bing_points
	cp ./* /usr/share/bing_points/
	cp ./bing_points.desktop /usr/share/applications/bing_points.desktop
	sed -i "s|^cd current_directory|cd $(shell pwd)|g" /usr/share/bing_points/bing_points.sh
	echo "Installation complete."

uninstall:
	rm -f /usr/share/applications/bing_points.desktop
	rm -rf /usr/share/bing_points
	echo "Uninstallation complete. Please remove this directory manually if needed."