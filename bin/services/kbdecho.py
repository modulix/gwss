#!/usr/bin/env python
from classes.SimpleService import SimpleService
from routr import route, POST, GET

class EchoService(SimpleService):
    """
    This service sends back received messages 
    """
    def action_kbdecho(self, msg):
        self.logger.debug("Echoing %s" % msg)
        self.reply(msg, {"action":"display", "data":msg["data"]})

def kbdecho(config):
    inst = EchoService("kbdecho", config)
    inst.public_actions = set(["kbdecho", "subscribe", "unsubscribe"])
    return inst
