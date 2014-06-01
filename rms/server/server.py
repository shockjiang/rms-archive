#!/usr/bin/env python
#encoding: utf-8

import signal
import service
import sys

from settings import get_host,log
    
def signal_handler(signal, frame):
    print('You pressed Ctrl+C! to stop the program')
    sys.exit()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    log.debug("RMS server started!")
    h = get_host()
    with open('common/testkey.pub') as f:
        s = service.CmdService(h, f.read())
    s.start()