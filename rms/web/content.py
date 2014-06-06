#!/usr/bin/env python
#encoding: utf-8

import sys
import json

import common.statuscode as statuscode
import ndn_client
from common.settings import get_host,log

class rmsContentClient(ndn_client.rmsClientBase):
    """RMS content management client"""

    QUERY_FAILED = -1
    FILE_EXIST = 0
    FILE_UPLOADING = 1
    FILE_NOT_FOUND = 2

    APP_NAME = "Content"
    def __init__(self, host, pemFile, timeout):
        super(rmsContentClient, self).__init__(host, rmsContentClient.APP_NAME, pemFile)
        self.cmd_timeout = timeout

    def send_cmd(self, dict_obj):
        self.Send(json.dumps(dict_obj), self.cmd_timeout)

    def DeleteFile(self, name):
        obj = {
            'op': 'delete',
            'name': name
        }
        self.send_cmd(obj)
        status, content = self.Recv(self.cmd_timeout)
        log.debug('status:{} content:{}'.format(status, content))
        return status == statuscode.STATUS_OK

    def SendFile(self, name, remotename, key):
        obj = {
            'op': 'send',
            'name': name,
            'remotename': remotename,
            'key': key
        }
        self.send_cmd(obj)
        status, content = self.Recv(self.cmd_timeout)
        log.debug('status:{} content:{}'.format(status, content))
        return status == statuscode.STATUS_OK

    def CheckFileState(self, name):
        obj = {
            'op': 'send',
            'name': name
        }
        self.send_cmd(obj)
        status, content = self.Recv(self.cmd_timeout)
        log.debug('status:{} content:{}'.format(status, content))
        if status != statuscode.STATUS_OK:
            return rmsContentClient.QUERY_FAILED

        if content == 'exist':
            return rmsContentClient.FILE_EXIST
        elif content == 'upload':
            return rmsContentClient.FILE_UPLOADING
        elif content == 'notfount':
            return rmsContentClient.FILE_NOT_FOUND
        else:
            log.debug('invalid response: {}'.format(content))
            return rmsContentClient.QUERY_FAILED

if __name__ == '__main__':
    client = None
    with open('common/testkey.pem') as f:
        client = rmsContentClient('local', f.read(), 2.0)

    client.Connect(6.0)
    if client.IsConnected():
        print client.SendFile('/cdn/c.mp3', '/flow_test/c.mp3', 'kkk')
        print client.SendFile('/cdn/img.jpg', '/flow_test/img.jpg', 'kkk')
        print client.SendFile('/cdn/txt.txt', '/flow_test/txt.txt', 'kkk')

    client.Stop()
