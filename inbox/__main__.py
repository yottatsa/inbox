#!/usr/bin/python3

import datetime

from .eml import Store
from .classifier import group_messages


DB = 'eml'
try:
    store = Store.load(DB)
except Exception as e:
    print(e)
    store = Store(DB)

def latest(g):
    group = g[1]
    return max((msg.metadata.date for msg in group.messages)), g[0], g[1]


def print_groups(groups):
    groups = map(latest, groups)
    groups = sorted(groups, key=lambda g: g[0], reverse=True)
    cutoff = groups[0][0] - datetime.timedelta(days=9)
    for ts, _, group in groups:
        if ts < cutoff:
            break
        title = group.titles.most_common(1)[0][0]
        print('*', title, f'/{len(group.messages)}')
        messages = sorted(
            group.messages, key=lambda m: m.metadata.date, reverse=True)
        for msg in messages:
            if msg.metadata.date < cutoff:
                break
            print('|  ', msg.metadata.date, msg.metadata.subject)


print_groups(group_messages(store).items())
store.save()
