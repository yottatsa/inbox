#!/usr/bin/python3

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import MeanShift
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer

from collections import Counter
from typing import Dict, NamedTuple, Any, Set, Tuple

from .eml import Store, Message

DEBUG = False

PROMO = {
    'newsletter@residentadvisor.net', 'product@news.digitalocean.com',
    'leo@email.lingualeo.com', 'noreply@kinohod.ru',
    'megafon@info.megafon.ru', 'notifications@bandsintown.com',
    'hsbc@email.hsbc.co.uk'
}


class BaseLabel(NamedTuple):
    titles: Counter
    label: str


class Label(BaseLabel):
    def size(self):
        return self.titles and sum(self.titles.values()) or 0

    def large(self):
        return self.size() > 3

    def small(self):
        return self.size() <= 2

    def __str__(self):
        sender = self.titles.most_common(1)[0][0]
        if '@' in sender:
            sender = sender.rsplit('@', 1)[1]
        if DEBUG:
            return f'{sender} ({self.label})'
        else:
            return sender

    def __hash__(self):
        return id(self)


class BaseConversation(NamedTuple):
    senders: Dict[str, str]
    ids: Set[str]


class Conversation(BaseConversation):
    def active(self):
        return len(self.senders) > 1

    def size(self):
        return len(self.ids)

    def large(self):
        return self.size() > 2

    def __str__(self):
        return ', '.join(sender.replace('@', ' ').split()[0].title()
                         for sender in self.senders.values())

    def merge(self, other):
        self.senders.update(other.senders)
        self.ids.update(other.senders)

    def __hash__(self):
        return id(self)


class Inquiry(object):

    def __init__(self, conversation, label):
        self.conversation = conversation
        self.label = label

    def __str__(self):
        return f'{self.label.__str__()}: {self.conversation.__str__()}'  # FIXME


class BaseComposite(object):

    def __init__(self, label):
        self.label = label

    def __str__(self):
        return self.__class__.__name__


class Promos(BaseComposite):
    pass


class Updates(BaseComposite):
    pass


Labels = Any


def group_messages_by_headers(store: Store) -> Store:
    index: Dict[Any, Conversation] = {}

    for msg in store.list_messages():
        emails = []
        emails.extend([mail_to[1].lower()
                       for mail_to in msg.metadata.mail_to
                       if mail_to[1]])
        if msg.metadata.mail_from and msg.metadata.mail_from[1]:
            emails.append(msg.metadata.mail_from[1].lower())

        keys = [tuple(sorted(emails))]
        keys.extend(msg.metadata.references)

        groups: Set[Conversation] = set()
        for ref in keys:
            if ref in index:
                groups.add(index[ref])

        group = groups and groups.pop() or Conversation(ids=set(), senders={})
        while groups:
            group.merge(groups.pop())

        for ref in keys:
            index[ref] = group

        group.ids.add(msg.msgid)
        if msg.metadata.mail_from and msg.metadata.mail_from[1]:
            group.senders[msg.metadata.mail_from[1]] = \
                msg.metadata.mail_from[0] or msg.metadata.mail_from[1]

        msg.labels['conversation'] = group

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
    labels: Dict[str, Label] = {}
    for msg, label_id in zip(messages, pipeline.named_steps['clust'].labels_):
        label = labels.setdefault(label_id, Label(label=label_id,
                                                  titles=Counter()))
        metadata = msg.metadata
        label.titles[metadata.mail_from[0] or metadata.mail_from[1]] += 1
        msg.labels['label'] = label
    return store


def group_messages(store: Store) -> Store:
    return group_messages_by_clustering(group_messages_by_headers(store))


def get_group(msg: Message) -> Tuple[Labels, str]:
    labels = msg.labels
    conversation: Conversation = labels['conversation']
    label = labels['label']
    if DEBUG:
        return label, msg.metadata.mail_from[1]
    else:
        mail_from = msg.metadata.mail_from[0] or msg.metadata.mail_from[1]
    if conversation.active():
        if label.size() > conversation.size():
            return Inquiry(label=label, conversation=conversation), mail_from
        return conversation, mail_from
    if (label.small() and label.size() < conversation.size()) or \
       PROMO.intersection(conversation.senders.keys()):
        return Promos(label=label), str(label)
    elif label.small():
        print('promo', label, conversation.senders)
    else:
        return Updates(label=label), str(label)
    return label, str(label)
