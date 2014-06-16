#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
@author: Xiaoke Jiang <shock.jiang@gmail.com>, 8 May,2014
This file amis to bild a framework of python project, especially when there are multiple files

@attention: This file MUST be placed on the root directory of python project 
@attention: This file MUST be sole file titled settings.py in the whole project
@attention: When other files need to import this file, this file SHOULD be the first one to be imported

@version: 0.1, Xiaoke Jiang, 8 May, 2014
'''

#from ndnflow.draft import settings

import sys
import os
import os.path  
import logging
import socket

MODE = 0 #0-debug, 1-run, 2+ undefined

ROOT_DIR = os.path.dirname(__file__)
if not ROOT_DIR in sys.path:
    sys.path.append(ROOT_DIR)
    print "put ROOT_DIR in path"
else:
    print "ROOT_DIR is already in path" 
    
OUTPUT_DIR = os.path.join(ROOT_DIR, 'output')
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    print "create the OUTPUT_DIR"
else:
    print "OUTPUT_DIR already exists"

OUT_DATA_DIR = os.path.join(OUTPUT_DIR, "data")
if not os.path.exists(OUT_DATA_DIR):
    os.makedirs(OUT_DATA_DIR)

OUT_FIG_DIR = os.path.join(OUTPUT_DIR, "fig")    
if not os.path.exists(OUT_FIG_DIR):
    os.makedirs(OUT_FIG_DIR)

INPUT_DIR = os.path.join(ROOT_DIR, 'input')
if not os.path.exists(INPUT_DIR):
    os.makedirs(INPUT_DIR)

DRAFT_DIR = os.path.join(ROOT_DIR, 'draft')
if not os.path.exists(DRAFT_DIR):
    os.makedirs(DRAFT_DIR)
    
RECYCLE_DIR = os.path.join(ROOT_DIR, 'recycle')
if not os.path.exists(RECYCLE_DIR):
    os.makedirs(RECYCLE_DIR)
    
SCRIPT_DIR = os.path.join(ROOT_DIR, 'script')
if not os.path.exists(SCRIPT_DIR):
    os.makedirs(SCRIPT_DIR)

    
TOOL_DIR = os.path.join(ROOT_DIR, 'tool')
if not os.path.exists(TOOL_DIR):
    os.makedirs(TOOL_DIR)

NOTE = os.path.join(ROOT_DIR, 'note.txt')
if not os.path.exists(NOTE):
    f = open(NOTE, "w")
    f.write("#this file is used to take notes of this project")
    f.close()
    
README = os.path.join(ROOT_DIR, 'README.txt')
if not os.path.exists(README):
    f = open(README, "w")
    f.write("#README, official hints of this project")
    f.close()



#logging.addLevelName( logging.INFO, "\x1b[01;34m %s" % logging.getLevelName(logging.INFO))
#logging.addLevelName( logging.DEBUG, "\033[1;41m%s\033[1;0m" % logging.getLevelName(logging.DEBUG))    
#ROOT_DIR = os.path.dirname((os.path.join(os.path.dirname(os.path.abspath("__file__")), os.path.pardir)))
log = logging.getLogger("ndnflow") #root logger, debug, info, warn, error, critical

#format = logging.Formatter('%(levelname)8s:%(funcName)23s:%(lineno)3d: %(message)s')
format = logging.Formatter('[%(levelname)5.5s:%(module)10.10s:%(funcName)10.10s:%(lineno)3d:%(asctime)s] %(message)s')
fh = logging.FileHandler("ndnflow.log", mode="w")
fh.setFormatter(format)
 
sh = logging.StreamHandler() #console
sh.setFormatter(format)
 
log.addHandler(sh)
log.addHandler(fh)
 
log.setLevel(logging.DEBUG)
#log.setLevel(logging.INFO)
#log.setLevel(logging.WARN)
#log.setLevel(logging.CRITICAL)

log.info("log in settings")



#extend settings
def get_host():
    hostname = socket.gethostname().strip()
    if hostname == "Shock-MBA.local" or hostname == "shockair.local":
        host = "local"
    elif hostname == "shock-vb":
        host = "guoao"
    elif hostname == "j06":
        host = "j06"
    elif hostname == "zhaogeng-OptiPlex-780":
        host = "l07"
    elif hostname == "ndngateway2":
        host = "tbed"
    elif hostname == "R710":   
        host = "super"
    elif hostname == "user-virtual-machine":
        host = "telcom"
    elif hostname == "shock-pc":
        host = "h243"
    elif hostname == "ndn":
        host = "h242"
    elif hostname == "ubuntuxyhu":
        host = "seu"
    elif hostname == "clarence-VirtualBox": #node is down
        host = "vt"
    elif hostname == "httpndn": #node is down
        host = "ushw"
    elif hostname == "ndngateway7": #node is down
        host = "h101"
    else:
        #host = hostname
        host = "local"

    return host
HOST = get_host()
log.info("local Host is %s" %(HOST))


class NDNRouter(object):
    def __init__(self, name, ip, port, username, password):
        self.name = name
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.workdir = "ndnflow"
    
    def __str__(self):
        return "%s" %(self.name)
    
ROUTERS = {"h243": NDNRouter("h243", "202.112.49.243", 6363, "none", "none"),
           "seu": NDNRouter("seu", "211.65.192.137", 6363, "none", "none"),
           "tbed": NDNRouter("tbed", "202.112.237.32", 6363, "none", "none"),
           "super": NDNRouter("super", "202.112.237.206", 6363, "none", "none"),
           "telcom": NDNRouter("telcom", "59.108.48.13", 6363, "none", "none"),
           "j06": NDNRouter("j06", "166.111.132.147", 6363, "none", "none"),
           "h101": NDNRouter("h101", "166.111.132.216", 6363, "none", "none"),
           "ushw": NDNRouter("ushw", "101.6.30.83", 6363, "none", "none"),
           }
def get_neighbors(name):
    if name == "h243":
        neighbors = ["tbed", "seu", "j06"]
    elif name == "j06":
        neighbors = ["h243", "h101", "ushw"]
    elif name == "h101":
        neighbors = ["seu", "j06", "ushw"]
    elif name == "seu":
        neighbors = ["super", "h243", "h101"]
    elif name == "super":
        neighbors = ["tbed", "seu", "telcom"]
    elif name == "tbed":
        neighbors = ["super", "h243", "telcom"]
    elif name == "telcom":
        neighbors = ["tbed", "super"]
    elif name == "ushw":
        neighbors = ["j06", "h101"]
    else:
        neighbors = ["h243"]
        
    return neighbors


