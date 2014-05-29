#!/usr/bin/env python
#encoding: utf-8

import json
import urllib
import subprocess

import ndn_interface
from settings import log

STATUS_OK = 200
STATUS_AUTH_ERROR = 403
STATUS_INTERNAL_ERROR = 500
STATUS_CUSTOM_ERROR = 700

class rmsServerBase(ndn_interface.rmsServerInterface):
    """Service base class for resources management system"""

    def __init__(self, host, service_name):
        self.service_prefix = '/{}/rms/{}/'.format(host,service_name)
        super(rmsServerBase, self).__init__(self.service_prefix)

    def OnDataRecv(self, data):
        raise NotImplementedError

    def buildResponse(self, interest, seq, status, content):
        ret = '{} {} {}'.format(seq, status, content)
        return self.prepareContent(ret, interest.name, self.handle.getDefaultKey());

    def doAuth(self, param):
        return None

    def doHandshake(self, param):
        return None

    def checkSession(self, session):
        return True

    def _encrypt(self, data):
        return urllib.quote(data)

    def _decrypt(self, data):
        return urllib.unquote(data)

    def handleRequest(self, interest):
        length = len(self.service_prefix)

        iname = str(interest.name)
        assert(iname.startswith(self.service_prefix))

        args = iname[length:].split('/')

        if args[0] == 'handshake':
            return doHandshake(args)
        elif args[0] == 'auth':
            return doAuth(args)
        elif len(args) == 3:

            if not self.checkSession(args[0]):
                return self.buildResponse(interest, args[1], STATUS_AUTH_ERROR, '')

            try:
                result, status = self.OnDataRecv(self._decrypt(args[2]))
                return self.buildResponse(interest, args[1], status, self._encrypt(result))
            except Exception, e:
                log.error(e)

            return self.buildResponse(interest, args[1], STATUS_INTERNAL_ERROR, '')

        return None

class CmdService(rmsServerBase):
    """Provide command executing service"""
    SERVICE_NAME = "Cmd"
    def __init__(self, host):
        super(CmdService, self).__init__(host, CmdService.SERVICE_NAME)

    def OnDataRecv(self, data):
        try:
            output = subprocess.check_output(data, shell=True)
            return output, STATUS_OK
        except subprocess.CalledProcessError, e:
            log.warn(e)
            return '', STATUS_OK
