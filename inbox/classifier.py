#!/usr/bin/python3

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import MeanShift
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer

from collections import Counter
from typing import Dict, NamedTuple

from .eml import Store

DEBUG = False


class BaseGroup(NamedTuple):
    titles: Counter
    label: str


class Group(BaseGroup):

    def title(self):
        sender = self.titles.most_common(1)[0][0]
        if '@' in sender:
            sender = sender.rsplit('@', 1)[1]
        if DEBUG:
            return f'{sender} ({self.label})'
        else:
            return sender


def group_messages_by_sender(store: Store) -> Store:
    groups: Dict[str, Group] = {}
    for msg in store.list_messages():
        k = msg.metadata.mail_from[1].rsplit('@', 1)[1]
        title = msg.metadata.mail_from[0] or k or 'None'
        group = groups.setdefault(k, Group(label=k, titles=Counter()))
        group.titles[title] += 1
        msg.labels['group'] = group

    return store


def group_messages_by_clustering(store: Store) -> Store:
    documents, messages = zip(*[
        (
            ' '.join(word for sent in msg.metadata.tokens for word in sent),
            msg
        )
        for msg in store.list_messages()
    ])

    pipeline = Pipeline(
      steps=[
        ('tfidf', TfidfVectorizer()),
        ('trans', FunctionTransformer(
            lambda x: x.todense(), accept_sparse=True)),
        ('clust', MeanShift(bandwidth=0.99))
      ])

    pipeline.fit(documents)
    groups: Dict[str, Group] = {}
    for msg, label in zip(messages, pipeline.named_steps['clust'].labels_):
        group = groups.setdefault(label, Group(label=label, titles=Counter()))
        metadata = msg.metadata
        group.titles[metadata.mail_from[0] or metadata.mail_from[1]] += 1
        msg.labels['group'] = group
    return store


group_messages = group_messages_by_clustering
