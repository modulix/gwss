#!/usr/bin/env python
from __future__ import print_function
import sys
import os
import time
import json
from datetime import datetime

class GWSSHandler():
    def __init__(self, client_service, environ, ws):
        self.logger = client_service.logger
        #super(GWSSHandler, self).__init__()
        #self.gwss = gwss
        self.ws = ws
        self.environ = environ
        self.client_service = client_service
        self.daemon = True
        self.listen = True
        ip = self.environ.get("HTTP_X_REAL_IP", self.environ.get("REMOTE_ADDR", "127.0.0.1"))
        self.address = "%s:%s" % (ip, self.environ.get("REMOTE_PORT"))
        self.logger.debug("GWSSHandler(%s):init" % id(self))
    def send(self,msg):
        try:
            self.ws.send(msg)
        except:
            self.listen = False
            pass
    def run(self):
        #self.gwss.logger.debug("GWSSHandler(%s) running..." % id(self))
        self.client_service.add_client(id(self), self)
        self.send(str(id(self)))
        while self.listen:
            try:
                message = self.ws.receive()
            except:
                message = None
                self.listen = False
                pass
                #sys.exc_clear()
            if message is None:
                self.logger.debug("GWSSHandler:Socket closed")
                self.listen = False
            else:
                self.logger.debug("GWSSHandler(%s):receive:%s" % (id(self),message))
                try:
                    msg = json.loads(message)
                except:
                    self.logger.debug("GWSSHandler(%s):error not valid JSON msg:%s" % (id(self),message))
                    continue
                try:
                    service = self.client_service.services[msg["service"]]
                    if msg["action"] not in service.public_actions:
                       continue
                    msg["source"] = {"service": self.client_service.name, "action":"send_client", "data": {"client":id(self)}}
                    self.client_service.send_action(msg)
                except Exception as e:
                    self.logger.debug(str(e))
        self.logger.debug("GWSSHandler(%s) stopping..." % id(self))
        self.client_service.del_client(self.address)
