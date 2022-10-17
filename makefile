.PHONY: pip default run

default: run

venv/bin/pip:
	virtualenv -p python2 venv

venv/bin/pip-sync venv/bin/pip-compile: venv/bin/pip
	venv/bin/pip install --upgrade pip
	venv/bin/pip install pip-tools ez_setup

requirements.txt: requirements.in venv/bin/pip-compile
	venv/bin/pip-compile requirements.in

venv/pip.touch: venv/bin/pip-sync requirements.txt
	venv/bin/pip-sync && touch $@

pip: venv/pip.touch

run: venv/pip.touch
	source venv/bin/activate && honcho start
