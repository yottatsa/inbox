#!/usr/bin/python3
from . import app


if __name__ == '__main__':
    app.run()
    app.store.save()
