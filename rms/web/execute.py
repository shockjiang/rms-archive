#!/usr/bin/env python
# -*- coding=utf-8 -*-

import sys
import urllib

import ndn_client

class rmsCmdClient(ndn_client.rmsClientBase):
    """RMS remote command executing client"""

    APP_NAME = "Cmd"
    def __init__(self, host):
        super(rmsCmdClient, self).__init__(host, rmsCmdClient.APP_NAME)

    def ExecuteWait(self, cmd, timeout = None):
        self.Send(cmd, timeout)
        status,content = self.Recv(timeout)
        return content


def usage():
    print("Usage: %s <hostname> <cmd>" % sys.argv[0])
    sys.exit(1)

if __name__ == '__main__':
    if (len(sys.argv) != 3):
        usage()

    client = rmsCmdClient(sys.argv[1])

    print(client.ExecuteWait(sys.argv[2], 5000))

