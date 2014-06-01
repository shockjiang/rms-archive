#!/usr/bin/env python
# -*- coding=utf-8 -*-

import sys
import urllib

import ndn_client

class rmsCmdClient(ndn_client.rmsClientBase):
    """RMS remote command executing client"""

    APP_NAME = "Cmd"
    def __init__(self, host, pemFile):
        super(rmsCmdClient, self).__init__(host, rmsCmdClient.APP_NAME, pemFile)

    def ExecuteWait(self, cmd, timeout = None):
        self.Send(cmd, timeout)
        status,content = self.Recv(timeout)
        return content


def usage():
    print("Usage: %s <hostname> <cmd>" % sys.argv[0])
    sys.exit(1)

if __name__ == '__main__':
    """Demo of rmsCmdClient"""

    if (len(sys.argv) != 3):
        usage()

    client = None
    with open('common/testkey.pem') as f:
        client = rmsCmdClient(sys.argv[1], f.read())

    client.Connect(4000)
    if client.IsConnected():
        print(client.ExecuteWait(sys.argv[2], 5000))
    else:
        print('Failed to connect')

