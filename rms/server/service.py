#!/usr/bin/env python
#encoding: utf-8

import uuid
import json
import urllib
import subprocess
from binascii import hexlify, unhexlify

import pylru

import common.security as security
import common.statuscode as statuscode
import ndn_interface
from common.settings import log


class SessionItem(object):
    def __init__(self, cipher):
        self.cipher = cipher
        self.seq = 0

    def session_encrypt_data(self, data):
        return self.cipher.encrypt(data)

    def session_decrypt_data(self, data):
        return self.cipher.decrypt(data)

class rmsServerBase(ndn_interface.rmsServerInterface):
    """Service base class for resources management system"""

    def __init__(self, host, service_name, pubFile):
        self.service_prefix = '/{}/rms/{}/'.format(host,service_name)
        self.auth_cache = pylru.lrucache(10)
        self.session_store = pylru.lrucache(100)
        self.pubFile = pubFile
        super(rmsServerBase, self).__init__(self.service_prefix)

    def OnDataRecv(self, data):
        raise NotImplementedError

    def newSession(self, cipher):
        session_id = str(uuid.uuid1())
        self.session_store[session_id] = SessionItem(cipher)
        return session_id

    def buildResponse(self, interest, seq, status, content):
        ret = '{} {} {}'.format(seq, status, content)
        return self.prepareContent(ret, interest.name, self.handle.getDefaultKey());

    def doAuth(self, param, interest):
        try:
            if param[1] in self.auth_cache:
                log.info("Received duplicated authorization request, ignored.")
                return None
            self.auth_cache[param[1]] = True

            auth = security.Auth()
            auth.setOtherDHKey(long(param[1], 0))
            randS, preMaster = auth.getDHKey(), auth.genPreMasterKey(self.pubFile)
            s = self.newSession(security.AESCipher(auth.genMasterKey()))
            ret = json.dumps(dict(
                randS = hex(randS),
                preMaster = hexlify(preMaster),
                session = s
                ))
            log.info("New client connected")
        except Exception, e:
            ret = ''
        return self.prepareContent(ret, interest.name, self.handle.getDefaultKey());

    def doHandshake(self, param, interest):
        return None

    def getSessionItem(self, session_id):
        return self.session_store[session_id]

    def handleRequest(self, interest):
        length = len(self.service_prefix)

        iname = str(interest.name)
        assert(iname.startswith(self.service_prefix))

        args = iname[length:].split('/')

        if args[0] == 'handshake':
            return self.doHandshake(args, interest)
        elif args[0] == 'auth':
            log.debug("'auth' interest received {}".format(args))
            return self.doAuth(args, interest)
        elif len(args) == 3:
            log.debug("interest received {}".format(args))
            (sid, seq, data) = tuple(args)
            seq = int(seq)
            s = self.getSessionItem(sid)
            if not s:
                log.warn("session not found")
                return self.buildResponse(interest, seq, statuscode.STATUS_AUTH_ERROR, '')
            if s.seq+1 != seq:
                log.error("sequence number error, {} expected, but {} received".format(s.seq+1, seq))
                return None
            else:
                s.seq += 1

            try:
                result, status = self.OnDataRecv(s.session_decrypt_data(data))
                return self.buildResponse(interest, seq, status, s.session_encrypt_data(result))
            except Exception, e:
                log.error(e)

            return self.buildResponse(interest, seq, statuscode.STATUS_INTERNAL_ERROR, '')

        return None

class CmdService(rmsServerBase):
    """Provide command executing service"""
    SERVICE_NAME = "Cmd"
    def __init__(self, host, pubFile):
        super(CmdService, self).__init__(host, CmdService.SERVICE_NAME, pubFile)

    def OnDataRecv(self, data):
        try:
            output = subprocess.check_output(data, shell=True)
            return output, statuscode.STATUS_OK
        except subprocess.CalledProcessError, e:
            log.warn(e)
            return '', statuscode.STATUS_OK
