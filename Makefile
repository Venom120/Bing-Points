.PHONY: run install uninstall

run:
	python -m venv .venv
	source .venv/bin/activate && pip install -r req.txt
	source .venv/bin/activate && python main.py

install:
	rm -rf /usr/share/bing_points
	mkdir /usr/share/bing_points
	
	cp main.py req.txt bing_points.sh bing_points.desktop /usr/share/bing_points/
	
	cd /usr/share/bing_points && python -m venv .venv
	cd /usr/share/bing_points && source .venv/bin/activate && pip install -r req.txt
	
	sed -i "s|cd current_directory|cd /usr/share/bing_points|g" /usr/share/bing_points/bing_points.sh
	
	cp /usr/share/bing_points/bing_points.desktop /usr/share/applications/bing_points.desktop
	echo "Installation complete."

uninstall:
	rm -f /usr/share/applications/bing_points.desktop
	rm -rf /usr/share/bing_points
	echo "Uninstallation complete. Please remove this directory manually if needed."