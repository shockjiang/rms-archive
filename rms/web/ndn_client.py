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
from common.settings import get_host,log

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

    def send(self, interest, timeout, retries = 3):
        self.retries = retries
        self.doSend(interest, timeout)

    def retry(self, interest):
        if not self.retries:
            self.recv_queue.put_nowait(QueueItem(interest, QueueItem.STATUS_TIME_OUT))
            return pyndn.RESULT_OK
        else:
            self.retries -= 1
            log.info('interest timed out, retrying...')
            return pyndn.RESULT_REEXPRESS

    def doSend(self, interest, timeout):
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
            return self.retry(upcallInfo.Interest.name)

        # make sure we're getting sane responses
        if not kind in [pyndn.UPCALL_CONTENT,
                        pyndn.UPCALL_CONTENT_UNVERIFIED,
                        pyndn.UPCALL_CONTENT_BAD]:
            log.error("Received invalid kind type: %d" % kind)
            return pyndn.RESULT_OK

        response_name = upcallInfo.ContentObject.name
        s = QueueItem.STATUS_OK

        if kind == pyndn.UPCALL_CONTENT_UNVERIFIED:
            s = QueueItem.STATUS_UNVERIFIED
        if kind == pyndn.UPCALL_CONTENT_BAD:
            s = QueueItem.STATUS_BAD

        self.recv_queue.put_nowait(QueueItem(response_name, s, upcallInfo.ContentObject.content))

        return pyndn.RESULT_OK

STATE_NOT_RUN = -1
STATE_NOT_AUTH = 0
STATE_IDLE = 1
STATE_WAIT_RECV = 2
class rmsClientBase(object):
    """Base class of RMS client application"""

    def __init__(self, host, app, pemFile):
        self.recv_queue = Queue.Queue()
        self.result_queue = Queue.Queue()
        self.name_prefix = "/{}/rms/{}".format(host, app)
        self.session_id = ''
        self.seq = 0
        self.isConnected = False
        self.pemFile = pemFile
        self.cipher = None
        self.state = STATE_NOT_RUN

        thread.start_new_thread(self._ndn_thread, tuple())
        #wait for thread to start
        while self.state == STATE_NOT_RUN:
            time.sleep(0)

    def _ndn_thread(self):
        self.ndn_interface = rmsClientInterface(self.recv_queue)
        self.state = STATE_NOT_AUTH
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
        if self.state != STATE_NOT_AUTH:
            raise ValueError
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
            self.state = STATE_IDLE
            thread.start_new_thread(self._recv_thread, tuple())
            log.debug('connect successfully')
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
        if self.state != STATE_IDLE:
            raise Exception('Not idle')
        data = self._encrypt(data)
        self.seq += 1
        self.state = STATE_WAIT_RECV
        self.ndn_interface.send(self.name_prefix + '/{}/{}/'.format(self.session_id, self.seq) + data, timeout)

    def _recv_thread(self):
        while True:
            try:
                item = self.recv_queue.get()
            except Exception, e:
                log.error(e)
                continue

            if item.status == QueueItem.STATUS_TIME_OUT:
                log.info("send timed out %s" % item.name)
                self.state = STATE_IDLE
                continue

            if self.state != STATE_WAIT_RECV:
                log.warn('content received in a wrong state %d'%self.state)
                continue

            if item.status in [QueueItem.STATUS_BAD, QueueItem.STATUS_UNVERIFIED]:
                log.warn('got bad content')
                self.state = STATE_IDLE
            elif item.status == QueueItem.STATUS_OK:
                log.debug('got content')
                try:
                    (seq, status, content) = self._decode_response(item.content)
                    seq = int(seq)
                except Exception, e:
                    log.error("unable to decode content, %s" % e)
                else:
                    if seq != self.seq:
                        log.warn("sequence number error, {} expected, but {} received".format(self.seq, seq))
                    else:
                        self.result_queue.put_nowait((status, content))
                        self.state = STATE_IDLE
            else:
                log.error('got unknown QueueItem')

    def Recv(self, timeout = None):
        """Receive data from server (may block)"""
        try:
            item = self.result_queue.get(True, timeout)
            return item
        except:
            return (None, None)

    def DiscardCurrentResult(self):
        if self.state != STATE_WAIT_RECV:
            log.warn('not waiting for result')
        else:
            self.state = STATE_IDLE

    def Stop(self):
        self.ndn_interface.stop()
