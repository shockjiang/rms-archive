#! /usr/bin/env python
# -*- coding=utf-8 -*-

import threading
import os
import sqlite3
import json
import time
from contextlib import closing
from binascii import hexlify, unhexlify
import hashlib

import webconfig
import execute
from common.settings import log

def connect_db():
    return sqlite3.connect(webconfig.DATABASE)

def getHostList():
    with closing(connect_db()) as db:
        cur = db.execute('select name from hosts order by id')
        entries = [row[0] for row in cur.fetchall()]
        return entries

class CmdLineBackend(object):
    class _monitor(threading.Thread):
        def __init__(self, clients):
            super(CmdLineBackend._monitor, self).__init__()
            self.clients = clients
            self.daemon = True

        def run(self):
            while True:
                time.sleep(5.0)
                for x in self.clients:
                    try:
                        if not x.IsConnected():
                            x.ReConnect(webconfig.NDN_CONNECT_TIMEOUT)
                    except Exception, e:
                        log.error(e)
            
    def __init__(self):
        self.hosts = getHostList()
        with open(webconfig.PRIVATE_KEY_FILE) as f:
            pem = f.read()
            self.clients = [execute.rmsCmdClient(h, pem) for h in self.hosts]

    def doConnect(self, client):
        try:
            client.Connect(webconfig.NDN_CONNECT_TIMEOUT)
        except Exception, e:
            log.error(e)
    
    def Start(self):
        # self.thread = _thread()
        # self.thread.start()
        
        log.info('Starting...')
        log.debug('Trying to connect servers')
        for x in self.clients:
            self.doConnect(x)
        CmdLineBackend._monitor(self.clients).start()

    def ExecuteOneCmd(self, host, cmd):
        idx = self.hosts.index(host)
        return self.clients[idx].ExecuteWait(str(cmd), webconfig.MOD_CMDLINE_TIMEOUT)

