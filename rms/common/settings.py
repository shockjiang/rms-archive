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

NDNFLOW_PATH = '$HOME/ndnflow'
NDNFLOW_CONTENT_PATH = '$HOME/ndnflow/dir'

log = logging.getLogger("ndnrms") #root logger, debug, info, warn, error, critical

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
# print "local Host is %s" %(HOST)

def get_ndnflow_path():
    return (os.path.expandvars(NDNFLOW_PATH),
        os.path.expandvars(NDNFLOW_CONTENT_PATH))

