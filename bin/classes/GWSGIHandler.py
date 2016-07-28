#!/usr/bin/env python
import sys
import os
import argparse
import logging
import logging.handlers
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
import logging

import config

#class GWSGIHandler(Thread):
class GWSGIHandler():
    """
    WSGI
    """
    def __init__(self, send_queue, environ, response):
        self.logger = logging.getLogger()
        #self.logger.debug("GWSGIHandler,(%s):init" % id(self))
        #super(GWSGIHandler, self).__init__()
        self.environ = environ
        self.response = response
        self.content = []
        self.ip = ""
        self.daemon = True
    def run(self):
        #self.logger.debug("GWSGIHandler(%s):running..." % id(self))
        try:
            self.ip = self.environ["HTTP_X_REAL_IP"]
        except:
            self.ip = self.environ["REMOTE_ADDR"]
        msg = ["Not found"]
        status = "404"
        response_headers = [("Content-type", "text/text"), ("Content-Length", str(len(msg)))]
        self.response(status, response_headers)
        if self.environ["PATH_INFO"][:len(config.api_url)] == config.api_url:
            #previously api path call
            pass
        else:
            file_name = os.path.join(os.path.join(os.path.expanduser(config.html_dir), self.environ["PATH_INFO"][1:]))
            ext = fname = ""
            (fname, ext) = os.path.splitext(file_name)
            #self.logger.debug("GWSGIHandler:%s(%s)" % (fname,ext))
            # Directories -> files.py
            module = action = ""
            if fname[-1] == "/":
                #self.logger.debug("GWSGIHandler:%s:trying %s or %s" % (self.environ["PATH_INFO"],"%s.py" % fname[:-1],"%s.py" % os.path.dirname(fname[:-1])))
                if os.path.isfile("%s.py" % fname[:-1]):
                    #self.logger.debug("GWSGIHandler:%s:->%s(3)" % (self.environ["PATH_INFO"],"%s.py" % fname[:-1]))
                    (module, action) = os.path.split(self.environ["PATH_INFO"][1:])
                elif os.path.isfile("%s.py" % os.path.dirname(fname[:-1])):
                    #self.logger.debug("GWSGIHandler:%s:->%s(2)" % (self.environ["PATH_INFO"],"%s.py" % os.path.dirname(fname[:-1])))
                    (module, action) = os.path.split(self.environ["PATH_INFO"][1:-1])
                elif os.path.isfile("%s/index.py" % fname[:-1]):
                    #self.logger.debug("GWSGIHandler:%s:->%s(1)" % (self.environ["PATH_INFO"],"%s/index.py" % fname[:-1]))
                    module = self.environ["PATH_INFO"][1:] + "index"
                else:
                    module = ""
            if module:
                module = module.replace("/",".")
                if not action:
                    action = "index"
                #self.logger.debug("GWSGIHandler:DIR:module=%s action=%s importing..." % (module, action))
                exec("from %s import %s" % (module, action))
                #self.logger.debug("GWSGIHandler:DIR:module=%s action=%s running..." % (module, action))
                exec("msg = %s(self, self.environ, self.response)" % action)
                status = "200 OK"
                response_headers = [("Content-type", "text/html"), ("Content-Length", str(len(msg)))]
                self.response(status, response_headers)
            elif os.path.isfile(file_name):
                # Python files
                if ext == ".py":
                    (module, action) = os.path.split(self.environ["PATH_INFO"][1:])
                    (action,ext) = os.path.splitext(action)
                    module = module.replace("/",".")
                    #self.logger.debug("GWSGIHandler:PY:module=%s action=%s" % (module, action))
                    if not module:
                        exec("from %s import index" % (action))
                        exec("msg = index(self, self.environ, self.response)")
                    else:
                        exec("from %s.%s import %s" % (module, action, action))
                        exec("msg = %s(self, self.environ, self.response)" % (action))
                    status = "200 OK"
                    response_headers = [("Content-type", "text/html"), ("Content-Length", str(len(msg)))]
                    self.response(status, response_headers)
                # Static files
                else:
                    # The header is set depending on extension of the file...
                    # Seems that ".svg" does not exist in standard mimetypes ?!
                    mimetypes.add_type('text/text', '.map')
                    mimetypes.add_type('images/svg+xml', '.svg')
                    mime = mimetypes.types_map[ext]
                    fd = open(file_name, "r")
                    msg = fd.read()
                    fd.close()
                    status = "200 OK"
                    response_headers = [("Content-type", mime), ("Content-Length", str(len(msg)))]
                    self.response(status, response_headers)
            else:
                # No static file, no python module...
                #self.logger.debug("GWSGIHandler:%s Not found"% (file_name))
                msg = status = "404 Not found"
                response_headers = [("Content-type", "text/text"), ("Content-Length", str(len(msg)))]
                self.response(status, response_headers)
        return(msg)
