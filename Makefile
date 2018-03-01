all: venv/requirements.txt run

.PHONY: all run

venv:
	python3 -m venv $@

venv/requirements.txt: requirements.txt venv
	./venv/bin/pip install -r $<
	cp $< $@

run: venv/requirements.txt
	rm -f eml/metadata.pickle
	sh -c '. ./venv/bin/activate; ./venv/bin/python3 -m inbox'
