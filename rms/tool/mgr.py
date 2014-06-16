#! /usr/bin/env python
# -*- coding=utf-8 -*-
'''
This script aims to manage for the host, especially to executes commands on all managed host  

@input

@output:

@e.g:
python mgr.py [-c cmd] [-d host1, host2, ...]

@author: Xiaoke Jiang <shock.jiang@gmail.com>
@version: 0.1, 28 May, 2014
'''

import argparse
import os
import sys
PAR_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not PAR_DIR in sys.path:
    sys.path.append(PAR_DIR)
    #print "add PAR_DIR"
else:
    pass
    #print "PAR_DIR is already in path"

import settings
from web.execute import Slurp
from datetime import datetime

class Session(Slurp):
    def __init__(self, host):
        self.host = host
        
        self.seq = 0
        self.session_id = str(datetime.now()) 
        self.user = "admin"
        
        self.cmds = []
        self.results = []
        
    def send_cmd(self, cmd):
        pass
    
    def get_result(self, kind, upcallInfo, **kwargs):
        pass
    
    def encrypt(self, msg):
        return msg

class Go(object):
    def __init__(self, hosts, **kwargs):
        self.hosts = hosts
        self.sessions = [Session(host=host) for host in self.hosts]
        
        
    def read(self):
        pass
    
    def save(self):
        pass
    
    def go(self, cmd):
        for session in self.sessions:
            session.send_cmd(cmd)
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Configure the arguments")
    parser.add_argument("-c", "--cmd", help="command to run on the host", default="ls")
    parser.add_argument("-d", "--hosts", nargs="+", help="the hosts which run the command", default=settings.ROUTERS.keys())
    
    args = parser.parse_args()
    
    go = Go(hosts=args.hosts)
    print args