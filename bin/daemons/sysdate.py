#!/usr/bin/env python
from classes.DaemonService import DaemonService
from datetime import datetime
import time

class SysdateService(DaemonService):
    """
    This service broadcast global sysdate to all subscribed clients
    """
    def main (self):
        while True:
            msg = datetime.now().strftime("%x %X")
            self.listen(1-0.001)
            for client in self.clientvars.keys():
                self.send_action("clients", "send_client", client=client, js_action="display", data={"id":"gwss_time", "value": msg})

def sysdate(config):
    return SysdateService("sysdate", config)
