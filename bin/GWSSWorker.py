#!/usr/bin/env python
import sys
from threading import Thread

class GWSSWorker(Thread):
    """
    This thread is in going to do the asked job
    thru code written in run def of ./services/xxxx.py file
    (xxxx is the service name)
    """
    def __init__(self, gwss, service, client, action, data):
        super(GWSSWorker, self).__init__()
        self.daemon = True
        self.gwss = gwss
        self.service = service
        self.client = client
        self.action = action
        self.data = data
    def run(self):
        self.gwss.logger.debug("%s:worker:%s" % (self.service.name, self.action))
        try:
            exec("from services import %s" % self.service.name)
            exec("%s.action(self.gwss, self.service, self.action, self.client, self.data)" % (self.service.name))
        except:
            #pass
            sys.exc_clear()
    #def __del__(self):
        #gwss.logger.debug("GWSSWorker dead")
