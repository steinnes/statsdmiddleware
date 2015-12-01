bootstrap:
	virtualenv venv
	venv/bin/pip install -r requirements.txt

run:
	venv/bin/python app.py


tcpdump:
	sudo tcpdump -A -i any port 8125
