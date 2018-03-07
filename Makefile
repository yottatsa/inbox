all: run

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

web/tether%:
	curl -L --create-dirs -o $@ https://cdnjs.cloudflare.com/ajax/libs/$(@:web/%=%)

~/nltk_data/tokenizers/punkt/README: venv/requirements.txt
	sh -c '. ./venv/bin/activate; python3 -c "import nltk; nltk.download(\"punkt\")"'
	touch $@

~/nltk_data/misc/perluniprops/Number.txt: venv/requirements.txt
	sh -c '. ./venv/bin/activate; python3 -c "import nltk; nltk.download(\"perluniprops\")"'
	touch $@

~/nltk_data/corpora/stopwords/README: venv/requirements.txt
	sh -c '. ./venv/bin/activate; python3 -c "import nltk; nltk.download(\"stopwords\")"'
	touch $@

bootstrap: \
	~/nltk_data/tokenizers/punkt/README \
	~/nltk_data/misc/perluniprops/Number.txt \
	web/react@16/umd/react.development.js \
	web/react-dom@16/umd/react-dom.development.js \
	web/babel-standalone@6.15.0/babel.min.js \
	web/bootstrap/4.0.0-alpha.6/css/bootstrap.min.css \
	web/bootstrap/4.0.0-alpha.6/css/bootstrap.min.css.map \
	web/bootstrap/4.0.0-alpha.6/js/bootstrap.min.js \
	web/tether/1.4.3/js/tether.min.js \
	web/jquery/jquery-3.3.1.min.js

clean:
	rm -f eml/metadata.pickle
	find inbox/__pycache__/ -name '*.pyc' -delete || :

run: clean bootstrap
	sh -c '. ./venv/bin/activate; python3 -m inbox'

.PHONY: all bootstrap clean run

