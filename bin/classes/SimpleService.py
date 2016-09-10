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
    def add_event(self, msg):
        self.exec_action(msg)
    def send_action(self, msg):
        service = msg.pop("service")
        if service in self.services:
            self.logger.debug("Sending to %s message: %s" % (service, str(msg)))
            self.services[service].add_event(msg)
        else:
            self.logger.info("Dropped message for unknown service: %s" % service)

