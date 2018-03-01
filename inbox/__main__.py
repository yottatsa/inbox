#!/usr/bin/python3

from .eml import Store

DB = 'eml'
try:
    store = Store.load(DB)
except Exception as e:
    print(e)
    store = Store(DB)

print([m.metadata for m in store.list_messages()])
store.save()

message = store.list_messages().__next__()
