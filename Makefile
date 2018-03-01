all: venv/requirements.txt

.PHONY: all

venv:
	python3 -m venv $@

venv/requirements.txt: requirements.txt venv
	./venv/bin/pip install -r $<
	cp $< $@
