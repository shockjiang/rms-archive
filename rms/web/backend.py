#! /usr/bin/env python
# -*- coding=utf-8 -*-

from copy import copy
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
import systool
from common.settings import log

def connect_db():
    return sqlite3.connect(webconfig.DATABASE)

def getHostList():
    # return ['local']
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


class SysMonitorBackend(object):
    class _thread(threading.Thread):
        def __init__(self):
            super(SysMonitorBackend._thread, self).__init__()
            self.daemon = True
            self.hosts = getHostList()
            self.mutex = threading.Lock()
            self.host_status = dict()
            with open(webconfig.PRIVATE_KEY_FILE) as f:
                pem = f.read()
                self.clients = [systool.rmsSysClient(h, pem) for h in self.hosts]

        def doConnect(self, client):
            try:
                client.Connect(webconfig.NDN_CONNECT_TIMEOUT)
            except Exception, e:
                log.error(e)

        def run(self):
            for x in self.clients:
                self.doConnect(x)
            while True:
                for i in range(len(self.clients)):
                    info = dict(alive = False, delay = None, updated = time.time())
                    try:
                        x = self.clients[i]
                        if not x.IsConnected():
                            x.ReConnect(webconfig.NDN_CONNECT_TIMEOUT)
                        info['alive'], info['delay'] = x.Ping()
                    except Exception, e:
                        log.error(e)

                    try:
                        self.mutex.acquire()
                        self.host_status[self.hosts[i]] = info
                    except Exception, e:
                        log.error(e)
                    finally:
                        try:
                            self.mutex.release()
                        except Exception, e:
                            pass

                log.debug("Monitor result: {}".format(self.host_status))
                time.sleep(webconfig.MOD_SYS_MONITOR_INTERVAL)

        def getHostStatus(self, h):
            s = None
            try:
                self.mutex.acquire()
                s = copy(self.host_status[h])
            except Exception, e:
                log.error(e)
            finally:
                try:
                    self.mutex.release()
                except Exception, e:
                    pass
            return s

        def reboot(self, h):
            try:
                i = self.hosts.index(h)
                self.clients[i].Reboot()
            except Exception, e:
                log.error(e)

    def __init__(self):
        self.thread = SysMonitorBackend._thread()

    def Start(self):
        self.thread.start()

    def GetHostStatus(self, h):
        return self.thread.getHostStatus(h)

    def RebootHost(self, h):
        self.thread.reboot(h)

