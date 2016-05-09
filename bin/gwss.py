#!/usr/bin/env python
from __future__ import print_function
import sys
import os
import time
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

VERSION = "0.3.0"
### BEGIN TUNABLES
server = "0.0.0.0"
port = 8888
api_url = "/api"
max_clients = 1000
#html_dir = "~/public_html"
#html_dir = "/var/www/html"
html_dir = "/usr/share/nginx/html"
logfile = "/var/log/nginx/gwss.log"
pidfile = "/var/run/gwss/gwss.pid"
sockname = "/var/run/gwss/gwss.sock"
### END TUNABLES

from threading import Thread
if sys.version_info.major == 2:
    #print("running Python 2.x")
    import urlparse

if sys.version_info.major == 3:
    #print("running Python 3.x")
    import urllib.parse as urlparse

from WebSocketServer import WebSocketServer
#from WebSocketService import WebSocketService
#from WebSocketWorker import WebSocketWorker

class GWSHandler():
    def __init__(self, gwss, environ, ws):
        gwss.logger.debug("gwss:GWSHandler(%s) Init" % id(self))
        self.gwss = gwss
        self.ws = ws
        self.environ = environ
        self.listen = True
    def send(self,msg):
        if self.listen and msg:
            self.ws.send(msg)
    def run(self):
        gwss.logger.debug("gwss:GWSHandler(%s) running..." % id(self))
        try:
            self.ip = self.environ["HTTP_X_REAL_IP"]
        except:
            self.ip = self.environ["REMOTE_ADDR"]
        self.gwss.add_client(self)
        while self.listen:
            message = self.ws.receive()
            if message is None:
                self.gwss.logger.debug("gwss:Socket closed {}".format(datetime.now().strftime("%H:%M:%S %f")))
                self.listen = False
            else:
                self.gwss.logger.debug("gwss:GWSHandler(%s):receive:%s" % (id(self),message))
                service = action = data = ""
                msg = json.loads(message)
                service = msg["service"]
                action = msg["action"]
                for svc in self.gwss.services:
                    if service == svc.name:
                        svc.receive(self, message)
        self.gwss.del_client(self)
    #def __del__(self):
        #gwss.logger.debug("gwss:GWSHandler(%d) dead" % id(self))

def GWSGIHandler(environ, response):
    """
    For each connection we use one of this handlers:
        WebSocket
        WSGI
    """
    msg = status = '404 Not found'
    response_headers = [("Content-type", "text/text"), ("Content-Length", str(len(msg)))]
    response(status, response_headers)
    try:
        if environ["HTTP_CONNECTION"].lower() == "upgrade" and environ["HTTP_UPGRADE"].lower() == "websocket":
            ws = environ["wsgi.websocket"]
        else:
            ws = False
    except:
        ws = False
    if ws:
        gwss.logger.debug("gwss:GWSGIHandler:%s: opening websocket..." % (environ["PATH_INFO"]))
        wshandler = GWSHandler(gwss, environ, ws)
        wshandler.run()
    else:
        # WebSocket management API
        if environ["PATH_INFO"][:len(api_url)] == api_url:
            try:
                (prefixe, service, action) = environ["PATH_INFO"][1:].split("/", 2)
                data = environ["QUERY_STRING"]
                gwss.logger.debug("gwss:%s: service=%s action=%s data=%s" % (environ["PATH_INFO"], service, action, data))
                req = urlparse.parse_qs(environ["QUERY_STRING"])
                data = {"id": req["id"][0], "value" : req["value"][0]}
                msg = "error:Service(%s) or action(%s) not found..." % (service, action)
                for svc in gwss.services:
                    if service == svc.name:
                        # Using the "api" function of ./services/service.py
                        exec("from services import %s" % service)
                        exec("%s.api(gwss, svc, action, data)" % service)
                        msg = status = "200 OK"
                        response_headers = [("Content-type", "text/html"), ("Content-Length", str(len(msg)))]
                        response(status, response_headers)
            except:
                pass
        else:
            file_name = os.path.join(os.path.join(os.path.expanduser(html_dir), environ["PATH_INFO"][1:]))
            ext = fname = ""
            (fname, ext) = os.path.splitext(file_name)
            gwss.logger.debug("gwss:GWSGIHandler:%s(%s)" % (fname,ext))
            # Directories -> files.py
            if os.path.isfile("%s.py" % fname[:-1]):
                (module, action) = os.path.split(environ["PATH_INFO"][1:])
                module = module.replace("/",".")
                gwss.logger.debug("gwss:GWSGIHandler:DIR:module=%s action=%s" % (module, action))
                if not action:
                    exec("from %s import index" % (module))
                    exec("msg = index(gwss, environ, response)")
                else:
                    exec("from %s import %s" % (module, action))
                    exec("msg = %s(gwss, environ, response)" % action)
                status = "200 OK"
                response_headers = [("Content-type", "text/html"), ("Content-Length", str(len(msg)))]
                response(status, response_headers)
            elif os.path.isfile(file_name):
                # Python files
                if ext == ".py":
                    (module, action) = os.path.split(environ["PATH_INFO"][1:])
                    (action,ext) = os.path.splitext(action)
                    module = module.replace("/",".")
                    gwss.logger.debug("gwss:GWSGIHandler:PY:module=%s action=%s" % (module, action))
                    if not module:
                        exec("from %s import index" % (action))
                        exec("msg = index(gwss, environ, response)")
                    else:
                        exec("from %s.%s import %s" % (module, action, action))
                        exec("msg = %s(gwss, environ, response)" % (action))
                    status = "200 OK"
                    response_headers = [("Content-type", "text/html"), ("Content-Length", str(len(msg)))]
                    response(status, response_headers)
                # Static files
                else:
                    # The header is set depending on extension of the file...
                    # Seems that ".svg" does not exist in standard mimetypes ?!
                    mimetypes.add_type('images/svg+xml', '.svg')
                    mime = mimetypes.types_map[ext]
                    fd = open(file_name, "r")
                    msg = fd.read()
                    fd.close()
                    status = "200 OK"
                    response_headers = [("Content-type", mime), ("Content-Length", str(len(msg)))]
                    response(status, response_headers)
            else:
                # No static file, no python module...
                gwss.logger.debug("gwss:GWSGIHandler:%s Not found"% (file_name))
                msg = status = "404 Not found"
                response_headers = [("Content-type", "text/text"), ("Content-Length", str(len(msg)))]
                response(status, response_headers)
        return([msg])

def main(args):
    try:
        os.mkdir(os.path.dirname(args.pidfile))
    except:
        pass
    fd = open(args.pidfile, "w")
    if fd:
        fd.write("%d" % os.getpid())
        fd.close()
    try:
        os.mkdir(os.path.dirname(args.sockname))
    except:
        pass
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    if os.path.exists(args.sockname):
        os.remove(args.sockname)
    listener.bind(args.sockname)
    listener.listen(1)

    # Starting WebSocket Server
    gevent.signal(signal.SIGQUIT, gevent.kill)
    gwss.start()
    gwss.logger.info("gwss:WebSocket Server running at http://%s:%s/" % (server, port))
    pool = Pool(max_clients)
    gwsgi = WSGIServer((server, port), GWSGIHandler, spawn=pool, handler_class=WebSocketHandler)
    gwsgi.serve_forever()
    gwss.logger.info("gwss:WebSocket Server stopped.")
    gwss.stop()
    gwss.join()
    del gwsgi
    return(0)

if __name__ == "__main__":
    """
    This is a the main of this multi-threaded daemon
    """
    # FS socket && Network socket
    argparser = argparse.ArgumentParser(prog='gwss')
    argparser.add_argument("--daemon", action="store_true", help="Run in background")
    argparser.add_argument("--syslog", action="store_true", help="Use syslog for logging")
    argparser.add_argument("--logfile", default=logfile, dest="logfile", action="store", help="File where to write logs")
    argparser.add_argument("--pidfile", default=pidfile, dest="pidfile", action="store", help="File where to write PID")
    argparser.add_argument("--sockname", default=sockname, dest="sockname", action="store", help="Create socket file")
    args = argparser.parse_args()

    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "services"))
    sys.path.insert(0, html_dir)

    logger = logging.getLogger("gwss")
    logger.setLevel(logging.DEBUG)
    if args.syslog:
        handler = logging.handlers.SysLogHandler(address = '/dev/log')
        log_format = logging.Formatter('%(levelname)s %(name)s[%(process)d]:%(asctime)s %(message)s')
    else:
        handler = logging.FileHandler(args.logfile)
        log_format = logging.Formatter('%(asctime)s ' + socket.getfqdn() + ' %(levelname)s %(name)s[%(process)d]: %(message)s')
    handler.setFormatter(log_format)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    logger.info("gwss: %s", "Starting...")
    gwss = WebSocketServer(logger)
    if args.daemon:
        pid = os.fork()
        if pid != 0:
            sys.exit(0)
    sys.exit(main(args))

