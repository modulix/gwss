#!/usr/bin/env python
from classes.SimpleService import SimpleService

class EchoService(SimpleService):
    """
    This service sends back received messages 
    """
    def action_kbdecho(self, msg):
        self.logger.debug("Echoing %s" % msg)
        self.reply(msg, {"action":"display", "data":msg["data"]})

def kbdecho(config):
    return EchoService("kbdecho", config)
