inbox
=====

1. Drop some messages into `eml/`
2. Run `make`

Requirements:
 * Python3
 * [emails](http://python-emails.readthedocs.io/en/latest/)
 * [html2text](https://pypi.python.org/pypi/html2text)
 * scikit-learn
 * reactjs
 * bootstrap
 * M2Crypto

todo
----

* Rendering
 - day-group-latest-count, where group is sender or category
 - show more context in the accordeon
 - Neat renderers for personal emails (image carousel, attach, preview)
 - Views to show context
* Categories
 - Thread-Topic
 - Personal Classifier
 - Pipelining
 - Promo detection: ngram-clf
* Core:
 - S/MIME reader
