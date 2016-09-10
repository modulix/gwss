#!/usr/bin/env python
from classes.DaemonService import DaemonService
import time

class PingService(DaemonService):
    """
    This service broadcast a ping to all subscribed clients
    """
    def main (self):
        while True:
            t = time.time()
            diff = 0
            while diff < 15:
                self.listen(15-diff)
                diff = time.time() - t
            for client in self.clientvars.keys() :
                self.send_action("clients", "send_client", client=client, js_action="ping", data={})

def ping(config):
    return PingService("ping", config)
