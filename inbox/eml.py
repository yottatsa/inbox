#!/usr/bin/python3

import codecs
import functools
import os
import sys
import datetime
import dateutil.parser
from typing import NamedTuple, Tuple, Dict, Optional, List, Any
import pickle
import emails.loader
from emails.loader.local_store import MsgLoader as MsgLoaderBase
from emails.loader.helpers import COMMON_CHARSETS
import emails.message
import lxml.html
import nltk
from nltk.tokenize.moses import MosesDetokenizer

detokenizer = MosesDetokenizer()
detokenize = detokenizer.detokenize
tokenize = nltk.tokenize.casual_tokenize
sent_tokenize = nltk.tokenize.sent_tokenize
stopwords = nltk.corpus.stopwords.words('english') +\
            nltk.corpus.stopwords.words('russian')
stemmer = nltk.stem.snowball.SnowballStemmer("english")


def words(sent: List[str]) -> List[str]:
    sent = [w.lower() for w in sent if w.isalpha()]
    sent = [stemmer.stem(w)
            for w in sent
            if w not in stopwords]
    return sent


def get_text(msg: str) -> Tuple[str, List[List[str]]]:
    page = lxml.html.document_fromstring(msg)

    for style in page.cssselect('style'):
        style.getparent().remove(style)
    msg = page.cssselect('body')[0].text_content()
    msg = msg.replace('---', ' ')
    msg = msg.replace('|', ' ')
    sents = sent_tokenize(msg)
    sents = [tokenize(sent) for sent in sents]
    msg = ' '.join((detokenize(sent, return_str=True) for sent in sents))
    tokens = [words(sent) for sent in sents]
    return msg, tokens


def get_domain_tokens(email: str) -> List[str]:
    if '@' not in email:
        return []
    result = email.rsplit('@', 1)
    result.extend(result[1].split('.'))
    return result


class MsgLoader(MsgLoaderBase):

    common_charsets = [sys.getdefaultencoding()]

    def filter_header(self, name):
        if name in ['date', 'message-id', 'references']:
            return True
        return super(MsgLoader, self).filter_header(name)

    def extract_part_text(self, part):
        charset = part.get_param('charset')
        cte = str(part.get('content-transfer-encoding', '')).lower()
        if charset == self.common_charsets[0] and not cte:
            return part.get_payload(decode=False)
        else:
            return self.decode_text(
                part.get_payload(decode=True),
                charset=part.get_param('charset')
            )[0]


class Metadata(NamedTuple):
    mail_from: Tuple[Optional[str], Optional[str]]
    mail_to: List[Tuple[Optional[str], Optional[str]]]
    subject: str
    date: datetime.datetime
    references: List[str]
    tokens: List[List[str]]
    preview: str


class Store(object):
    METADATA_FILE = 'metadata.pickle'

    def __init__(self, db: str) -> None:
        self.db = db
        self.metadata: Dict[str, Metadata] = {}
        self.labels: Dict[str, Any] = {}
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
        if encoding and encoding != self.encodings[0]:
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

    def list_messages(self) -> List['Message']:
        return [
            Message(self, f)
            for f in os.listdir(self.db)
            if f.endswith('.eml')
        ]


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
        subject = message.subject.replace('\r\n', '')
        text, tokens = get_text(message.html or message.text)
        tokens.append(words(tokenize(subject)))
        mdtoken = []
        if message.mail_from[0]:
            mdtoken.extend(words(tokenize(message.mail_from[0])))
        if message.mail_from[1]:
            mdtoken.append(message.mail_from[1])
            mdtoken.extend(get_domain_tokens(message.mail_from[1]))
        tokens.append(mdtoken)
        for r in message.mail_to:
            if r[0]:
                tokens.append(words(tokenize(r[0])))
            tokens.append(r[1])

        references = [
            r for r in message._headers.get('references', '').split() if r
        ]
        message_id = message._headers.get('message-id', '').strip()
        if message_id:
            references.append(message_id)

        metadata = Metadata(
            mail_from=message.mail_from,
            mail_to=message.mail_to,
            subject=subject,
            date=dateutil.parser.parse(message._headers['date']),
            references=references,
            tokens=tokens,
            preview=text[:200],
        )
        self.store.metadata[self.msgid] = metadata
        return metadata

    @property
    def labels(self) -> Dict[str, Any]:
        return self.store.labels.setdefault(self.msgid, {})

    @property
    @functools.lru_cache()
    def message(self) -> emails.message.Message:
        message = emails.loader.from_rfc822(
            self.store.reader(self.msgid),
            MsgLoader,
            parse_headers=True,
        )
        return message
