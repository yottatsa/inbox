#!/usr/bin/python3

import os
import flask
import datetime
import arrow

from .classifier import group_messages


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
        first_date = None
        for msg in sorted(
            group_messages(store).list_messages(),
            key=lambda msg: msg.metadata.date,
            reverse=True
        ):
            if not first_date:
                first_date = msg.metadata.date
            if first_date - msg.metadata.date > datetime.timedelta(days=7):
                date = arrow.get(msg.metadata.date).ceil('week').humanize()
            else:
                date = arrow.get(msg.metadata.date).ceil('day').humanize()

            if not prev_date or prev_date != date:
                topics = []
                messages.append({'date': date, 'topics': topics})
                topics_messages = {}
                prev_date = date
            title = msg.labels['group'].title()
            if title not in topics_messages:
                avatar = os.path.join('avatars', f'{title}.png')
                topics.append({
                    'from': title,
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
                                'subject': msg.metadata.subject,
                                'preview': msg.metadata.preview,
                            })

        return flask.json.jsonify({'messages': messages})

    return app
