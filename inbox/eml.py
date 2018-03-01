#!/usr/bin/python3

import codecs
import functools
import os
import datetime
import dateutil.parser
from typing import NamedTuple, Tuple, Dict, Optional, List
import pickle
import emails.loader
from emails.loader.local_store import MsgLoader as MsgLoaderBase
from emails.loader.helpers import COMMON_CHARSETS
import emails.message
import html2text

h2t = html2text.HTML2Text()
h2t.ignore_links = True
h2t.ignore_tables = True


def get_text(msg: str) -> str:
    msg = h2t.handle(msg)
    msg = msg.replace('-', ' ')
    msg = msg.replace('|', ' ')
    return ' '.join(msg.split())


class MsgLoader(MsgLoaderBase):
    def filter_header(self, name):
        if name in ['date']:
            return True
        return super(MsgLoader, self).filter_header(name)


class Metadata(NamedTuple):
    mail_from: Tuple[Optional[str], Optional[str]]
    mail_to: List[Tuple[Optional[str], Optional[str]]]
    subject: str
    date: datetime.datetime
    tokens: str


class Store(object):
    METADATA_FILE = 'metadata.pickle'

    def __init__(self, db: str) -> None:
        self.db = db
        self.metadata: Dict[str, Metadata] = {}
        self.encodings = COMMON_CHARSETS[1:]
        self.encoding_metadata: Dict[str, str] = {}

    @classmethod
    def load(cls, db: str):
        store = cls(db)
        with open(store._filename(cls.METADATA_FILE), 'rb') as f:
            store.__dict__.update(pickle.load(f))
        return store

    def save(self):
        with open(self._filename(self.METADATA_FILE), 'wb') as f:
            pickle.dump(self.__dict__, f)

    def _get_encoding(self, path: str) -> List[str]:
        encoding = self.encoding_metadata.get(path)
        if encoding:
            return [encoding]
        else:
            return self.encodings

    def _update_encoding(self, path: str, encoding: str) -> None:
        if encoding != self.encodings[0]:
            self.encoding_metadata[path] = encoding
        elif path in self.encoding_metadata:
            del self.encoding_metadata[path]

    def _filename(self, path: str) -> str:
        return os.path.join(self.db, path)

    def reader(self, path: str) -> str:
        filename = self._filename(path)
        last_exception: Optional[Exception] = None
        for encoding in self._get_encoding(path):
            try:
                with codecs.open(filename, 'r', encoding) as f:
                    content = f.read()
                self._update_encoding(path, encoding)
                return content
            except (UnicodeDecodeError, UnicodeError) as e:
                last_exception = e
        if last_exception:
            raise ValueError from last_exception

    def list_messages(self):
        return (
            Message(self, f)
            for f in os.listdir(self.db)
            if f.endswith('.eml')
        )


class Message(object):
    def __init__(self, store: Store, msgid: str) -> None:
        self.store = store
        self.msgid = msgid

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.msgid} {self.metadata}>'

    @property
    def metadata(self) -> Metadata:
        if self.msgid in self.store.metadata:
            return self.store.metadata[self.msgid]
        message = self.message
        email = message.mail_from[1]
        subject = message.subject.replace('\r\n', '')
        text = get_text(message.html or message.text)
        tokens = [
            email and email.rsplit('@', 1)[1], email,
            message.mail_from[0],
            subject,
            text
        ]
        for r in message.mail_to:
            tokens.extend(r)

        metadata = Metadata(
            mail_from=message.mail_from,
            mail_to=message.mail_to,
            subject=subject,
            date=dateutil.parser.parse(message._headers['date']),
            tokens=' '.join(filter(lambda i: i is not None, tokens)),
        )
        self.store.metadata[self.msgid] = metadata
        return metadata

    @property
    @functools.lru_cache()
    def message(self) -> emails.message.Message:
        message = emails.loader.from_rfc822(
            self.store.reader(self.msgid),
            MsgLoader,
            parse_headers=True,
        )
        return message
