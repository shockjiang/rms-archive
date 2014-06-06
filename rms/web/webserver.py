#! /usr/bin/env python
# -*- coding=utf-8 -*-

import os
import sqlite3
import json
from contextlib import closing
from binascii import hexlify, unhexlify
import hashlib

from flask import Flask, send_from_directory, url_for, abort
from flask import request
from werkzeug.routing import BaseConverter

import webconfig
import backend
from common.settings import log

class RegexConverter(BaseConverter):

    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


app = Flask(__name__)
app.url_map.converters['regex'] = RegexConverter

backend_cmd = None
backend_sys = None
backend_content = None

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


#handle static files
@app.route('/<regex("(js|css|partials|font-awesome|fonts)"):d>/<path:path>', methods=['GET'])
def static_proxy(d, path):
    return send_from_directory('webroot/' + d, path)


#==========host related operations==========
@app.route('/api/hostlist')
def api_hostlint():
    with closing(connect_db()) as db:
        cur = db.execute('select name from hosts order by id')
        entries = [dict(name=row[0]) for row in cur.fetchall()]
        return json.dumps(entries)
    abort(500)


#==========command related operations==========
@app.route('/api/execute/<host>/<cmd>')
def api_execute(host, cmd):
    try:
        cmd = unhexlify(cmd)
        ret = backend_cmd.ExecuteOneCmd(host, cmd)
        if ret == None:
            raise ValueError
        return json.dumps(dict(text=ret))
    except Exception, e:
        log.error(e)
        abort(500)

#==========content management related operations==========
@app.route('/api/content/<hosts>/<Filter>', methods=['GET'])
@app.route('/api/content/<hosts>', methods=['GET'])
@app.route('/api/content', methods=['GET'])
def api_content_list(hosts = '', Filter = None):
    hosts = hosts.split(',')
    result = []
    with closing(connect_db()) as db:
        placeholders = ','.join('?'*len(hosts))
        sql = 'SELECT DISTINCT content.name FROM content JOIN hosts ON (hosts.id = content.host_id) WHERE hosts.name IN (%s)' % placeholders
        if Filter:
            Filter = unhexlify(Filter)
            sql += ' AND content.name LIKE ?'
            hosts.append(str(Filter)+'%')

        cur = db.execute(sql, hosts)
        entries = [dict(c=row[0]) for row in cur.fetchall()]
        return json.dumps(entries)

@app.route('/api/content/<hosts>/<name>', methods=['DELETE'])
def api_content_del(hosts, name):
    name = unhexlify(name)
    hosts = hosts.split(',')

    # ask hosts to delete file
    hosts = filter(lambda h:backend_content.DeleteFiles(h,name), hosts)
    log.debug("successfully deleted {}: {}".format(name,hosts))

    with closing(connect_db()) as db:
        placeholders = ','.join('?'*len(hosts))
        sql = 'DELETE FROM content WHERE id IN (SELECT content.id FROM content JOIN hosts ON (hosts.id = content.host_id) WHERE hosts.name IN (%s) AND content.name=?)' % placeholders
        hosts.append(name)
        db.execute(sql, hosts)
        db.commit()
        return '{"error": 0}'

@app.route('/api/content/<hosts>/<name>', methods=['POST'])
def api_content_upload(hosts, name):
    try:
        hosts = hosts.split(',')
        name = unhexlify(name)
        files = request.files['file']

        backend_content.PublishFiles(hosts, name, files)

        with closing(connect_db()) as db:
            placeholders = ','.join('?'*len(hosts))
            sql = 'SELECT id FROM hosts WHERE hosts.name IN (%s)' % placeholders
            cur = db.execute(sql, hosts)
            entries = [row[0] for row in cur.fetchall()]
            for x in entries:
                try:
                    db.execute('INSERT INTO content(host_id,name) VALUES (?,?)', (x, name))
                except sqlite3.IntegrityError:
                    pass
            db.commit()

        return '{"error": 0}'
    except Exception, e:
        raise e

#==========system management related operations==========
@app.route('/api/sys/<hosts>/reboot', methods=['GET'])
def api_sys_reboot(hosts):
    try:
        hosts = hosts.split(',')
        for x in hosts:
            backend_sys.RebootHost(x)

        return '{"error": 0}'

    except Exception, e:
        log.error(e)
        raise e

@app.route('/api/sys/*/status', methods=['GET'])
def api_sys_all_status():
    try:
        with closing(connect_db()) as db:
            cur = db.execute('select name from hosts order by id')
            result = dict()
            for row in cur.fetchall():
                result[row[0]] = backend_sys.GetHostStatus(row[0])
            return json.dumps(result)
    except Exception, e:
        log.error(e)
        raise e

#==========default page==========
@app.route('/')
def index_handler():
    return send_from_directory('webroot', 'index.html')

if __name__ == '__main__':
    global backend_cmd, backend_sys
    backend_sys = backend.SysMonitorBackend()
    backend_content = backend.ContentManagementBackend()
    backend_cmd = backend.CmdLineBackend()
    backend_cmd.Start()
    backend_content.Start()
    backend_sys.Start()
    app.run(host=webconfig.LISTEN_IP, debug=webconfig.DEBUG, use_reloader=False, threaded=True)
