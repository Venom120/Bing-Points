.PHONY: install uninstall

install:
	chmod +rx ./bing_points.sh
	python -m venv .venv
	source .venv/bin/activate && pip install -r req.txt
	cp ./bing_points.desktop /usr/share/applications/bing_points.desktop
	cp ./bing_points.sh /usr/bin/bing_points
	sed -i "s|^cd current_directory|cd $(shell pwd)|g" /usr/bin/bing_points

uninstall:
	rm -f /usr/share/applications/bing_points.desktop
	rm -f /usr/bin/bing_points
	echo "Uninstallation complete. Please remove this directory manually if needed."
