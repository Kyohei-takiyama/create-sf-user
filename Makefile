VENV := venv

create-venv:
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -r requirements.txt

clean:
	rm -rf $(VENV)

run:
	make create-venv
	$(VENV)/bin/pip install -r requirements.txt
	ENV=dev $(VENV)/bin/python3 src/main.py
	make clean

run-prod:
	make create-venv
	$(VENV)/bin/pip install -r requirements.txt
	ENV=prod $(VENV)/bin/python3 src/main.py
	make clean