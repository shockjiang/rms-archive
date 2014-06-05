#!/usr/bin/env python
# -*- coding=utf-8 -*-

import sys
import urllib
import time

import ndn_client

class rmsSysClient(ndn_client.rmsClientBase):
    """RMS system management client"""

    APP_NAME = "Sys"
    def __init__(self, host, pemFile):
        super(rmsSysClient, self).__init__(host, rmsSysClient.APP_NAME, pemFile)

    def Ping(self):
        s = time.clock()
        self.Send('ping', 3.0)
        status, content = self.Recv(2.0)
        if status == None or content != 'ping':
            return False, 'Timed out'
        s = time.clock() - s
        return True, '%fms' % (s*1000)

    def Reboot(self):
        self.Send('reboot', 3.0)
        status, content = self.Recv(2.0)


def usage():
    print("Usage: %s <hostname> (ping|reboot)" % sys.argv[0])
    sys.exit(1)

if __name__ == '__main__':
    """Demo of rmsSysClient"""

    if (len(sys.argv) < 3):
        usage()

    client = None
    with open('common/testkey.pem') as f:
        client = rmsSysClient(sys.argv[1], f.read())

    client.Connect(6.0)
    if client.IsConnected():
        if sys.argv[2] == 'ping':
            print(client.Ping())
        elif sys.argv[2] == 'reboot':
            print(client.Reboot())
        else:
            usage()
    else:
        print('Failed to connect')

    client.Stop()
