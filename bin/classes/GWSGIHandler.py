#!/usr/bin/env python
import sys
import os
import argparse
from datetime import datetime

import json
import signal
import mimetypes
import gevent
from gevent import socket
from geventwebsocket.handler import WebSocketHandler
from gevent.pywsgi import WSGIServer
from gevent.pool import Pool
#from gevent.lock import Semaphore
#from gevent.server import StreamServer
from threading import Thread

class GWSGIHandler():
    """
    WSGI
    """
    def __init__(self, logger, html_dir, environ, response):
        self.logger = logger
        self.html_dir = html_dir
        self.logger.debug("GWSGIHandler,(%s):init" % id(self))
        self.environ = environ
        self.response = response
        self.content = []
        self.ip = ""
    def run(self):
        self.logger.debug("GWSGIHandler(%s):running..." % id(self))
        try:
            self.ip = self.environ["HTTP_X_REAL_IP"]
        except:
            self.ip = self.environ["REMOTE_ADDR"]

        self.logger.debug("GWSGIHandler:Answering request %s" % self.environ["PATH_INFO"])
        msg = "Not found"
        status = "404"
        mime = "text/text"
        file_name = os.path.join(os.path.expanduser(self.html_dir), self.environ["PATH_INFO"][1:])
        if os.path.isfile(file_name):
            (fname, ext) = os.path.splitext(file_name)
            # The header is set depending on extension of the file...
            # Seems that ".svg" does not exist in standard mimetypes ?!
            mimetypes.add_type('text/text', '.map')
            mimetypes.add_type('images/svg+xml', '.svg')
            mime = mimetypes.types_map[ext]
            fd = open(file_name, "r")
            msg = fd.read()
            fd.close()
            status = "200 OK"
        else:
            # No static file, no python module...
            self.logger.debug("GWSGIHandler:%s Not found"% (file_name))
        response_headers = [("Content-type", mime), ("Content-Length", str(len(msg)))]
        self.response(status, response_headers)
        return(msg)
