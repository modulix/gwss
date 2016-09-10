#!/usr/bin/env python
import json
from BaseService import BaseService

class SimpleService(BaseService):
    """
    No daemon mode.
    This service's actions are expected to be non-blocking,
    otherwise the server will stall during them. 
    """
    def __init__(self, *args):
        super(SimpleService, self).__init__(*args)
        self.services = {}
        #Groups of clients (used for all client pushes)
    def add_event(self, action, data):
        self.exec_action(action, data)
    def send_action(self, service, action, **kwargs):
        if service in self.services:
            self.logger.debug("send_action service %s action %s data %s" % (service, action, str(kwargs)))
            self.services[service].add_event(action, kwargs)

