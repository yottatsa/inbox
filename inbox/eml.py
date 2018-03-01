#!/usr/bin/python3

import codecs
import functools
import os
import datetime
import dateutil.parser
from typing import NamedTuple, Tuple, Dict, Optional, List
import pickle

import emails.loader
import emails.message


class Metadata(NamedTuple):
    mail_from: Tuple[str, str]
    subject: str
    date: datetime.datetime


class Store(object):
    METADATA_FILE = 'metadata.pickle'

    def __init__(self, db: str) -> None:
        self.db = db
        self.metadata: Dict[str, Metadata] = {}
        self.encodings = ['utf-8', 'windows-1252']
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
            except UnicodeDecodeError as e:
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

    @property
    def metadata(self) -> Metadata:
        if self.msgid in self.store.metadata:
            return self.store.metadata[self.msgid]
        message = self.message
        metadata = Metadata(
            mail_from = message.mail_from,
            subject = message.subject,
            date = dateutil.parser.parse(message.date)
        )
        self.store.metadata[self.msgid] = metadata
        return metadata

    @property
    @functools.lru_cache()
    def message(self) -> emails.message.Message:
        message = emails.loader.from_rfc822(
            self.store.reader(self.msgid),
            parse_headers=True,
        )
        return message
