#!/usr/bin/python3
from .app import App
from .eml import Store
from .classifier import group_messages


DB = 'eml'


try:
    store = Store.load(DB)
except Exception as e:
    store = Store(DB)

store.list_messages()
store.save()

app = App(__name__, store)
