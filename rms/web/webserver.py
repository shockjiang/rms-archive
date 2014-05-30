#! /usr/bin/env python
# -*- coding=utf-8 -*-

import os
import sqlite3
import json
from contextlib import closing

from flask import Flask, send_from_directory, url_for, abort
from werkzeug.routing import BaseConverter

import webconfig
import execute


class RegexConverter(BaseConverter):

    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


app = Flask(__name__)
app.url_map.converters['regex'] = RegexConverter


def connect_db():
    return sqlite3.connect(webconfig.DATABASE)


@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response


@app.route('/<regex("(js|css|partials|font-awesome|fonts)"):d>/<path:path>', methods=['GET'])
def static_proxy(d, path):
    return send_from_directory('webroot/' + d, path)


@app.route('/api/hostlist')
def api_hostlint():
    with closing(connect_db()) as db:
        cur = db.execute('select name from hosts order by id')
        entries = [dict(name=row[0]) for row in cur.fetchall()]
        return json.dumps(entries)
    abort(500)


@app.route('/api/execute/<host>/<cmd>')
def api_execute(host, cmd):
    try:
        client = execute.rmsCmdClient(str(host))
        ret = client.ExecuteWait(str(cmd), 5000)
        if ret == None:
            raise ValueError
        return json.dumps(dict(text=ret))
    except Exception, e:
        print(e)
        abort(500)


@app.route('/')
def index_handler():
    return send_from_directory('webroot', 'index.html')

if __name__ == '__main__':
    app.run(host=webconfig.LISTEN_IP, debug=webconfig.DEBUG)
