#!/usr/bin/env python
#encoding: utf-8

import base64
import urllib
import subprocess

import ndn_interface
from settings import log

RESULT_EXCEPTION = -1
RESULT_OK = 0
RESULT_INVALID_PARAM = 1

class rmsService(ndn_interface.rmsInterface):

    """Service base class for resources management system"""

    def __init__(self, service_name):
        self.service_prefix = service_name
        super(rmsService, self).__init__(service_name)

    def doCommand(self):
        return ''

    def handleRequest(self, interest):
        length = len(self.service_prefix)
        iname = str(interest.name)
        assert(iname[0:length] == self.service_prefix)

        args = iname[length:] if self.service_prefix[-1] =='/' else iname[length + 1:]
        args = args.split('/')

        try:
            print(args)
            result = self.doCommand(*args)
            if result == None:
                raise ValueError()
            return (RESULT_OK, self.prepareContent(result, interest.name, self.handle.getDefaultKey()))
        except Exception, e:
            log.error(e)

        return (RESULT_EXCEPTION, '')

class CmdService(rmsService):
    """Provide command executing"""
    def __init__(self, host):
        super(CmdService, self).__init__('/'+host+"/rms/cmd")

    def doCommand(self, enc, cmd):
        if enc == 'base64':
            cmd = base64.b64decode(cmd);    
        elif enc == 'url':
            cmd = urllib.unquote(cmd)
        else:
            log.error("CmdService: Unknown encoding")
            return 'Unknown encoding'

        output = subprocess.check_output(cmd, shell=True)

        return output


if __name__ == '__main__':
    s = rmsService("/local/rms/cmd")
    s.start()
