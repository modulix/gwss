#!/usr/bin/env python
import json
from BaseService import BaseService
from multiprocessing import Process, Pipe
import traceback

class DaemonService(BaseService):
    """
    In charge to receive messages and send responses to subscribed clients
    """
    def __init__(self, name, config):
        super(DaemonService, self).__init__(name, config)
        self.proc = Process(target=self.main)
        self.proc.daemon = True
        self.parent_end, self.child_end = Pipe()
        self.listen_fileno = self.parent_end.fileno()
        self.proc.start()
    def listen (self, timeout=None):
        if not self.child_end.poll(timeout):
            return
        msg = self.child_end.recv()
        self.exec_action(msg)
    def add_event(self, msg):
        self.logger.debug("Piping message: %s" % msg)
        self.parent_end.send(msg)
    def send_action(self, msg):
        self.child_end.send(msg)
    def recv_action(self):
        return self.parent_end.recv()

