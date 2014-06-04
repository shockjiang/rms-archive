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

    def ExecuteWait(self, cmd, cmd_timeout = None, send_timeout = 1.0):
        self.Send(cmd, send_timeout)
        status,content = self.Recv(cmd_timeout)
        if status == None:
            self.DiscardCurrentResult()
            return 'Executing timed out'
        return content


def usage():
    print("Usage: %s <hostname> [cmd ...]" % sys.argv[0])
    sys.exit(1)

if __name__ == '__main__':
    """Demo of rmsCmdClient"""

    if (len(sys.argv) < 2):
        usage()

    client = None
    with open('common/testkey.pem') as f:
        client = rmsCmdClient(sys.argv[1], f.read())

    client.Connect(6.0)
    if client.IsConnected():
        if len(sys.argv) >= 3:
            for x in xrange(len(sys.argv)-2):
                print(client.ExecuteWait(sys.argv[2 + x], 5.0))
        else:
            while True:
                try:
                    cmd = raw_input('$')
                    if not cmd: break
                except:
                    break
                print(client.ExecuteWait(cmd, 5.0))
    else:
        print('Failed to connect')

    client.Stop()
