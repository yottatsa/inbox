inbox
=====

Smart Inbox for Hosted Mail.

1. Drop some messages into `eml/`
2. Run `make`

Requirements:
 * Python3
   - [babel](http://babel.pocoo.org)
   - [emails](http://python-emails.readthedocs.io/en/latest/)
   - flask
   - nltk
   - scikit-learn
   - M2Crypto
 * JS
   - babel
   - bootstrap
   - reactjs

todo
----

* Rendering
  - day-[category]-label-messages
  - show less in line, show more context in the accordeon
  - greedy renderer for promos
  - Neat renderers for personal emails (image carousel, attach, preview)
* Categories
  - Team: set of senders > 1
  - Conversation (subject)
  - Time
  - Cluster label
    o Protogroup: set of ungroupables within short period of time 
  - Pipelining
* Core:
  - S/MIME reader
