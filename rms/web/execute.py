#!/usr/bin/env python
#encoding: utf-8

#
# Copyright (c) 2011, Regents of the University of California
# BSD license, See the COPYING file for more information
# Written by: Derek Kulinski <takeda@takeda.tk>
#

import sys
import urllib

import pyndn

class Slurp(pyndn.Closure):
    def __init__(self, root, handle = None):
        self.root = pyndn.Name(root)
        self.handle = handle or pyndn.NDN()

    def start(self, timeout):
        templ = pyndn.Interest()
        templ.answerOriginKind = 0
        templ.childSelctor = 1
        self.handle.expressInterest(self.root, self, templ)
        self.handle.run(timeout)

    def upcall(self, kind, upcallInfo):

        if kind == pyndn.UPCALL_FINAL:
            # any cleanup code here (so far I never had need for
            # this call type)
            return pyndn.RESULT_OK

        if kind == pyndn.UPCALL_INTEREST_TIMED_OUT:
            print("Got timeout!")
            return pyndn.RESULT_OK

        # make sure we're getting sane responses
        if not kind in [pyndn.UPCALL_CONTENT,
                        pyndn.UPCALL_CONTENT_UNVERIFIED,
                        pyndn.UPCALL_CONTENT_BAD]:
            print("Received invalid kind type: %d" % kind)
            sys.exit(100)

        response_name = upcallInfo.ContentObject.name
        if kind == pyndn.UPCALL_CONTENT_BAD:
            print("*** VERIFICATION FAILURE *** %s" % response_name)

        print(upcallInfo.ContentObject.content)

        self.handle.setRunTimeout(0)

        return pyndn.RESULT_OK

def usage():
    print("Usage: %s <hostname> <cmd>" % sys.argv[0])
    sys.exit(1)

if __name__ == '__main__':
    if (len(sys.argv) != 3):
        usage()

    host = sys.argv[1]
    req = '/' + host + '/rms/cmd/url/'+urllib.quote(sys.argv[2])
    timeout = 5000

    slurp = Slurp(req)
    slurp.start(timeout)
