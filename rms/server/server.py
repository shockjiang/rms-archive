#!/usr/bin/env python
#encoding: utf-8

import signal
import service

from settings import get_host,log
    
def signal_handler(signal, frame):
    print('You pressed Ctrl+C! to stop the program')
    sys.exit()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    log.debug("RMS server started!")
    h = get_host()
    s = service.CmdService(h)
    s.start()