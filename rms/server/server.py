#!/usr/bin/env python
#encoding: utf-8

import signal
import service
import sys
import threading

from common.settings import get_host,log
    
def signal_handler(signal, frame):
    print('You pressed Ctrl+C! to stop the program')
    sys.exit()

class cmd_service_thread(threading.Thread):
    def __init__(self, hostname):
        super(cmd_service_thread, self).__init__()
        self.daemon = True
        self.hostname = hostname

    def run(self):
        with open('common/testkey.pub') as f:
            s = service.CmdService(self.hostname, f.read())
        s.start()

class sys_service_thread(threading.Thread):
    def __init__(self, hostname):
        super(sys_service_thread, self).__init__()
        self.daemon = True
        self.hostname = hostname

    def run(self):
        with open('common/testkey.pub') as f:
            s = service.SystemService(self.hostname, f.read())
        s.start()

class content_service_thread(threading.Thread):
    def __init__(self, hostname):
        super(content_service_thread, self).__init__()
        self.daemon = True
        self.hostname = hostname

    def run(self):
        with open('common/testkey.pub') as f:
            s = service.ContentService(self.hostname, f.read())
        s.start()

if __name__ == "__main__":
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    h = get_host()
    cmd_service_thread(h).start()
    sys_service_thread(h).start()
    content_service_thread(h).start()
    log.debug("RMS server started!")
    signal.signal(signal.SIGINT, signal_handler)

    import time
    while True:
        time.sleep(1)