inbox
=====

1. Drop some messages into `eml/`
2. Run `make`

Requirements:
 * Python3
   - arrow
   - [emails](http://python-emails.readthedocs.io/en/latest/)
   - flask
   - nltk
   - scikit-learn
   - M2Crypto
 * JS
   - reactjs
   - bootstrap

todo
----

* Rendering
  - day-[category]-label-messages
  - show more context in the accordeon
  - Neat renderers for personal emails (image carousel, attach, preview)
* Categories
  - Team: set of senders > 1
  - Conversation (subject and Thread-Topic)
  -  Time
  -  Cluster label
     o Company: set of labels with similars senders
     o Pitch: unique label in Company 
     o Protogroup: set of ungroupables within short period of time 
  - Pipelining
* Core:
  - S/MIME reader
