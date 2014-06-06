#!/usr/bin/env python
#encoding: utf-8

import uuid
import json
import urllib
import subprocess
import threading
import sys
import Queue
import os
import os.path
from binascii import hexlify, unhexlify

import pylru

import common.security as security
import common.statuscode as statuscode
import ndn_interface
from common.settings import log, get_ndnflow_path
sys.path.append(get_ndnflow_path()[0])
import ndn_flow

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
        try:
            return self.session_store[session_id]
        except KeyError:
            return None

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

class SystemService(rmsServerBase):
    """Handle system management request"""
    SERVICE_NAME = "Sys"
    def __init__(self, host, pubFile):
        super(SystemService, self).__init__(host, SystemService.SERVICE_NAME, pubFile)

    def OnDataRecv(self, data):
        if data == 'ping':
            return 'ping', statuscode.STATUS_OK
        elif data == 'reboot':
            log.info('Rebooting...')
            os.execl(sys.executable, *([sys.executable]+sys.argv))
            return 'failed', statuscode.STATUS_CUSTOM_ERROR

class ContentService(rmsServerBase):
    """Content management service"""
    SERVICE_NAME = "Content"
    def __init__(self, host, pubFile):
        super(ContentService, self).__init__(host, ContentService.SERVICE_NAME, pubFile)
        self.ndnflow_dir = get_ndnflow_path()[1]
        self.thread = ContentService.content_service_thread()
        self.thread.start()

    class content_service_thread(threading.Thread):
        def __init__(self):
            super(ContentService.content_service_thread, self).__init__()
            self.daemon = True
            self.uploading_queue = Queue.Queue()
            self.uploading_set = set()
            self.uploading_mutex = threading.Lock()

        def run(self):
            while True:
                try:
                    (name, remotename, key) = self.uploading_queue.get()
                except:
                    continue
                try:
                    with open(name, 'wb') as f:
                        consumer = ndn_flow.FlowConsumer(999, str(remotename), fout=f)
                        consumer.start()
                except Exception, e:
                    log.error("failed to fetch file: %s" % e)
                    # import traceback
                    # traceback.print_exc()
                    try:
                        os.unlink(name)
                    except Exception, e:
                        log.error("cannot delete %s %s" % (name,e))
                finally:
                    self.mark_uploading(name, False)

        def mark_uploading(self, name, b):
            self.uploading_mutex.acquire()
            try:
                if b:
                    log.debug('set uploading mark %s' % name)
                    self.uploading_set.add(name)
                else:
                    log.debug('remove uploading mark %s' % name)
                    self.uploading_set.remove(name)
            except Exception, e:
                log.error(e)
            finally:
                self.uploading_mutex.release()

        def new_uploading(self, name, remotename, key):
            self.mark_uploading(name, True)
            try:
                self.uploading_queue.put_nowait((name, remotename, key))
            except Exception, e:
                log.error("failed to put into queue: %s" % e)
                self.mark_uploading(name, False)
    
    def name2filepath(self, name):
        #TODO: restrict file in ndnflow_dir
        while name.startswith('/'):
            name = name[1:]
        p = os.path.join(self.ndnflow_dir, name)
        log.debug('name:{} path:{}'.format(name, p))
        return p

    def OnDataRecv(self, data):
        req = json.loads(data)
        if req['op'] == 'delete':
            name = self.name2filepath(req['name'])
            try:
                os.unlink(name)
                return 'ok', statuscode.STATUS_OK
            except Exception, e:
                log.warn('Deleting {}: {}'.format(name, e))
                return str(e), statuscode.STATUS_CUSTOM_ERROR
        elif req['op'] == 'send':
            name = self.name2filepath(req['name'])
            self.thread.new_uploading(name, req['remotename'], req['key'])
            return 'ok', statuscode.STATUS_OK

        else:
            return 'unknown operation', statuscode.STATUS_CUSTOM_ERROR
