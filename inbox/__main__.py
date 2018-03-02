#!/usr/bin/python3
from .app import App


app = App(__name__)
app.run()
app.store.save()
