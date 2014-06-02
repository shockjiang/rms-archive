#! /usr/bin/env python
# -*- coding=utf-8 -*-

import Queue
import thread
import json
import urllib
import time
from binascii import hexlify, unhexlify

import pyndn

import common.security as security

class QueueItem(object):

    STATUS_OK = 0
    STATUS_UNVERIFIED = 1
    STATUS_BAD = 2
    STATUS_TIME_OUT = 3

    def __init__(self, name, status, content = None):
        self.name = name
        self.status = status
        self.content = content


class rmsClientInterface(pyndn.Closure):
    def __init__(self, recv_queue):
        self.handle = pyndn.NDN()
        self.recv_queue = recv_queue

    def send(self, interest, timeout):
        templ = pyndn.Interest()
        templ.answerOriginKind = 0
        templ.childSelctor = 1
        templ.interestLifetime = timeout
        self.handle.expressInterest(pyndn.Name(interest), self, templ)

    def start(self, timeout = -1):
        self.handle.run(timeout)

    def stop(self):
        self.handle.setRunTimeout(0)

    def upcall(self, kind, upcallInfo):

        if kind == pyndn.UPCALL_FINAL:
            return pyndn.RESULT_OK

        if kind == pyndn.UPCALL_INTEREST_TIMED_OUT:
            self.recv_queue.put_nowait(QueueItem(upcallInfo.Interest.name, QueueItem.STATUS_TIME_OUT))
            return pyndn.RESULT_OK

        # make sure we're getting sane responses
        if not kind in [pyndn.UPCALL_CONTENT,
                        pyndn.UPCALL_CONTENT_UNVERIFIED,
                        pyndn.UPCALL_CONTENT_BAD]:
            print("Received invalid kind type: %d" % kind)
            return pyndn.RESULT_OK

        response_name = upcallInfo.ContentObject.name
        s = QueueItem.STATUS_OK

        if kind == pyndn.UPCALL_CONTENT_UNVERIFIED:
            s = QueueItem.STATUS_UNVERIFIED
        if kind == pyndn.UPCALL_CONTENT_BAD:
            s = QueueItem.STATUS_BAD

        self.recv_queue.put_nowait(QueueItem(response_name, s, upcallInfo.ContentObject.content))

        return pyndn.RESULT_OK


class rmsClientBase(object):
    """Base class of RMS client application"""

    def __init__(self, host, app, pemFile):
        self.recv_queue = Queue.Queue()
        self.name_prefix = "/{}/rms/{}".format(host, app)
        self.session_id = ''
        self.seq = 0
        self.isConnected = False
        self.pemFile = pemFile
        self.cipher = None

        self.thread_started = False
        thread.start_new_thread(self._ndn_thread, tuple())
        while not self.thread_started:
            time.sleep(0)

    def _ndn_thread(self):
        self.ndn_interface = rmsClientInterface(self.recv_queue)
        self.thread_started = True
        self.ndn_interface.start()

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
        self.ndn_interface.send(self.name_prefix + '/auth/{}'.format(hex(auth.getDHKey())), timeout)

        try:
            reply = self.recv_queue.get(True, timeout)
            if reply.status != QueueItem.STATUS_OK:
                raise ValueError('Authorization with server failed')
            data = json.loads(reply.content)

            auth.setOtherDHKey(long(data['randS'], 0))
            auth.decryptPreMasterKey(unhexlify(data['preMaster']), self.pemFile)
            self.cipher = security.AESCipher(auth.genMasterKey())
            
            self.session_id = data['session']
            self.isConnected = True
        except Queue.Empty:
            raise Exception('Authorization timed out')
        except Exception, e:
            raise e

    def IsConnected(self):
        return self.isConnected

    def Send(self, data, timeout):
        """Send data to server (may block)"""
        if not self.isConnected:
            raise Exception('Not connected to server')
        data = self._encrypt(data)
        self.ndn_interface.send(self.name_prefix + '/{}/{}/'.format(self.session_id, self.seq) + data, timeout)
        self.seq += 1

    def Recv(self, timeout = None):
        """Receive data from server (may block)"""
        try:
            item = self.recv_queue.get(True, timeout)
            if item.status != QueueItem.STATUS_OK:
                return None, None
            data = item.content
            (seq, status, content) = self._decode_response(data)
            return (status, content)
        except Exception, e:
            print e
            return None, None

    def Stop(self):
        self.ndn_interface.stop()
