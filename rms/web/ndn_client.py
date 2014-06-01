#! /usr/bin/env python
# -*- coding=utf-8 -*-

import Queue
import thread
import json
import urllib
from binascii import hexlify, unhexlify

import pyndn

import common.security as security

class rmsClientInterface(pyndn.Closure):
    def __init__(self, root, recv_queue):
        self.root = pyndn.Name(root)
        self.handle = pyndn.NDN()
        self.recv_queue = recv_queue

    def start(self, timeout):
        templ = pyndn.Interest()
        templ.answerOriginKind = 0
        templ.childSelctor = 1
        self.handle.expressInterest(self.root, self, templ)
        self.handle.run(timeout)

    def upcall(self, kind, upcallInfo):

        if kind == pyndn.UPCALL_FINAL:
            self.recv_queue = None
            return pyndn.RESULT_OK

        if kind == pyndn.UPCALL_INTEREST_TIMED_OUT:
            print("Got timeout!")
            return pyndn.RESULT_OK

        # make sure we're getting sane responses
        if not kind in [pyndn.UPCALL_CONTENT,
                        pyndn.UPCALL_CONTENT_UNVERIFIED,
                        pyndn.UPCALL_CONTENT_BAD]:
            print("Received invalid kind type: %d" % kind)
            return pyndn.RESULT_OK

        response_name = upcallInfo.ContentObject.name
        if kind == pyndn.UPCALL_CONTENT_BAD:
            print("*** VERIFICATION FAILURE *** %s" % response_name)

        self.recv_queue.put_nowait(upcallInfo.ContentObject.content)

        self.handle.setRunTimeout(0)

        return pyndn.RESULT_OK


class rmsClientBase(object):
    """Base class of RMS client application"""

    def __init__(self, host, app, pemFile):
        self.recv_queue = Queue.Queue()
        self.name_prefix = "/{}/rms/{}".format(host, app)
        self.session_id = 'deadbeef'
        self.seq = 0
        self.isConnected = False
        self.pemFile = pemFile
        self.cipher = None

    def _ndn_thread(self, interest, timeout):
        rmsClientInterface(interest, self.recv_queue).start(timeout)

    def _pass2ndn(self, interest, timeout):
        thread.start_new_thread(self._ndn_thread, (interest, timeout))

    def _encrypt(self, data):
        return self.cipher.encrypt(data)

    def _decrypt(self, data):
        return self.cipher.decrypt(data)

    def _decode_response(self, data):
        space1 = data.find(' ')
        if space1 == -1:
            raise ValueError
        space2 = data.find(' ', space1+1)
        if space2 == -1:
            raise ValueError
        return (int(data[0:space1]), int(data[space1+1:space2]), self._decrypt(data[space2+1:]))

    def Connect(self, timeout):
        """Shake hand and authorize with server (may block)"""
        auth = security.Auth()
        self.isConnected = False
        self._pass2ndn(self.name_prefix + '/auth/{}'.format(hex(auth.getDHKey())), timeout)

        try:
            reply = self.recv_queue.get(True, timeout/1000.0)
            data = json.loads(reply)
            auth.setOtherDHKey(long(data['randS'], 0))
            auth.decryptPreMasterKey(unhexlify(data['preMaster']), self.pemFile)
            self.cipher = security.AESCipher(auth.genMasterKey())
            self.isConnected = True
        except Queue.Empty:
            raise Exception('Timed out')
        except Exception, e:
            raise e

    def IsConnected(self):
        return self.isConnected

    def Send(self, data, timeout):
        """Send data to server (may block)"""
        if not self.isConnected:
            raise Exception('Not connected to server')
        data = self._encrypt(data)
        self._pass2ndn(self.name_prefix + '/{}/{}/'.format(self.session_id, self.seq) + data, timeout)
        self.seq += 1

    def Recv(self, timeout = None):
        """Receive data from server (may block)"""
        try:
            if timeout != None:
                timeout = timeout/1000.0 #ms->s
            data = self.recv_queue.get(True, timeout)
            (seq, status, content) = self._decode_response(data)
            return (status, content)
        except Exception, e:
            return None, None
