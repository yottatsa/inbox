#!/usr/bin/python3

import os
import flask
import datetime
from babel.dates import format_timedelta

from .classifier import group_messages, get_group


def root_dir():
    return os.path.abspath(os.path.dirname(__file__))


def latest(g):
    group = g[1]
    return max((msg.metadata.date for msg in group.messages)), g[0], g[1]


def App(name, store):
    app = flask.Flask(name)
    app.store = store
    avatar_cache = {}
    no_avatar = os.path.join('avatars', '__empty__.png')

    @app.route('/')
    def hello():
        return flask.redirect(
            flask.url_for('static', filename='index.html'),
            code=302
        )

    @app.route('/api/messages.json')
    def messages():
        messages = []
        prev_date = None
        now = datetime.datetime.now(datetime.timezone.utc)
        for msg in sorted(
            group_messages(store).list_messages(),
            key=lambda msg: msg.metadata.date,
            reverse=True
        ):
            if not now:
                now = msg.metadata.date
            delta = now - msg.metadata.date
            if delta < datetime.timedelta(days=7):
                date = format_timedelta(delta,
                                        granularity='day', locale='en_US')
            elif delta < datetime.timedelta(days=30):
                date = format_timedelta(delta,
                                        granularity='week', locale='en_US')
            else:
                date = format_timedelta(delta,
                                        granularity='month', locale='en_US')

            if not prev_date or prev_date != date:
                topics = []
                messages.append({'date': date, 'topics': topics})
                topics_messages = {}
                prev_date = date
            group, sender = get_group(msg)
            title = str(group)
            if title not in topics_messages:
                avatar = os.path.join('avatars', f'{title}.png')
                topics.append({
                    'view': group.__class__.__name__.lower(),
                    'title': title,
                    'avatar': avatar_cache.setdefault(
                        title,
                        os.path.exists(os.path.join(
                            root_dir(),
                            'static',
                            avatar
                        )) and avatar or no_avatar
                    ),
                    'messages': topics_messages.setdefault(title, []),
                })
            topics_messages[title].append({
                                'sender': sender,
                                'subject': msg.metadata.subject,
                                'preview': msg.metadata.preview,
                            })

        return flask.json.jsonify({'messages': messages})

    return app
