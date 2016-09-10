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
            for env in self.clientvars:
                self.reply(env["source"],{"action":"ping"})

def ping(config):
    return PingService("ping", config)
