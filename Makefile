all: build run

venv:
	python3 -m venv $@

venv/requirements.txt: requirements.txt venv
	./venv/bin/pip install -r $<
	cp $< $@

web/react%.js web/babel%.js:
	curl -L --create-dirs -o $@ https://unpkg.com/$(@:web/%=%)

web/bootstrap%:
	curl -L --create-dirs -o $@ https://maxcdn.bootstrapcdn.com/$(@:web/%=%)

web/jquery%:
	curl -L --create-dirs -o $@ https://code.jquery.com/$(@:web/jquery/%=%)

build: venv/requirements.txt web/react@16/umd/react.development.js web/react-dom@16/umd/react-dom.development.js web/babel-standalone@6.15.0/babel.min.js web/bootstrap/4.0.0/css/bootstrap.min.css web/bootstrap/4.0.0/css/bootstrap.min.css.map web/jquery/jquery-3.3.1.min.js

run: build
	rm -f eml/metadata.pickle
	sh -c '. ./venv/bin/activate; ./venv/bin/python3 -m inbox'

.PHONY: all build run

