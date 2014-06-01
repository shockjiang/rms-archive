#!/usr/bin/env python
#encoding: utf-8

import json
import urllib
import subprocess
from binascii import hexlify, unhexlify

import common.security as security
import ndn_interface
from settings import log

STATUS_OK = 200
STATUS_AUTH_ERROR = 403
STATUS_INTERNAL_ERROR = 500
STATUS_CUSTOM_ERROR = 700

class rmsServerBase(ndn_interface.rmsServerInterface):
    """Service base class for resources management system"""

    def __init__(self, host, service_name, pubFile):
        self.service_prefix = '/{}/rms/{}/'.format(host,service_name)
        self.cipher = None
        self.pubFile = pubFile
        super(rmsServerBase, self).__init__(self.service_prefix)

    def OnDataRecv(self, data):
        raise NotImplementedError

    def buildResponse(self, interest, seq, status, content):
        ret = '{} {} {}'.format(seq, status, content)
        return self.prepareContent(ret, interest.name, self.handle.getDefaultKey());

    def doAuth(self, param, interest):
        try:
            auth = security.Auth()
            auth.setOtherDHKey(long(param[1], 0))
            randS, preMaster = auth.getDHKey(), auth.genPreMasterKey(self.pubFile)
            self.cipher = security.AESCipher(auth.genMasterKey())
            ret = json.dumps(dict(randS = hex(randS), preMaster = hexlify(preMaster)))
        except Exception, e:
            ret = ''
        return self.prepareContent(ret, interest.name, self.handle.getDefaultKey());

    def doHandshake(self, param, interest):
        return None

    def checkSession(self, session):
        return True

    def _encrypt(self, data):
        return self.cipher.encrypt(data)

    def _decrypt(self, data):
        return self.cipher.decrypt(data)

    def handleRequest(self, interest):
        length = len(self.service_prefix)

        iname = str(interest.name)
        assert(iname.startswith(self.service_prefix))

        args = iname[length:].split('/')

        if args[0] == 'handshake':
            return self.doHandshake(args, interest)
        elif args[0] == 'auth':
            return self.doAuth(args, interest)
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
    def __init__(self, host, pubFile):
        super(CmdService, self).__init__(host, CmdService.SERVICE_NAME, pubFile)

    def OnDataRecv(self, data):
        try:
            output = subprocess.check_output(data, shell=True)
            return output, STATUS_OK
        except subprocess.CalledProcessError, e:
            log.warn(e)
            return '', STATUS_OK
