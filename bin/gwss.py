#!/usr/bin/env python
from __future__ import print_function
import sys
import os
import signal
import argparse
import json
from datetime import datetime

import gevent
from gevent import socket
from geventwebsocket.handler import WebSocketHandler
from gevent.pywsgi import WSGIServer
from gevent.pool import Pool
#from gevent.lock import Semaphore
#from gevent.server import StreamServer

import logging
import logging.handlers
from threading import Thread

if sys.version_info.major == 2:
    #print("running Python 2.x")
    import urlparse

if sys.version_info.major == 3:
    #print("running Python 3.x")
    import urllib.parse as urlparse

from GWSServer import GWSServer
from GWSSHandler import GWSSHandler
from GWSGIHandler import GWSGIHandler

VERSION = "0.4.0"
### BEGIN TUNABLES
import config
### END TUNABLES

def gwss_dispatch(environ, response):
    """
    For each connection we use one of this handlers:
        WebSocket
        WSGI
    """
    url = environ["PATH_INFO"]
    ws = False
    try:
        if environ["HTTP_CONNECTION"].lower() == "upgrade" and environ["HTTP_UPGRADE"].lower() == "websocket":
            ws = environ["wsgi.websocket"]
    except:
        pass
    # This is a websocket request (we need to maintain this connection)
    if ws:
        gwss.logger.debug("gwss:dispatch:%s: opening WebSocket..." % (url))
        # So this can NOT be run in a separate thread...
        wshandler = GWSSHandler(gwss, environ, ws)
        gevent.spawn(wshandler.run())
        return(None)
    # This is not a websocket request
    else:
        gwss.logger.debug("gwss:dispatch:%s: opening WSGI..." % (url))
        wsgihandler = GWSGIHandler(gwss, environ, response)
        msg = wsgihandler.run()
        # WebSocket management API
        #status = "200"
        #response_headers = [("Content-type", mime), ("Content-Length", str(len(msg)))]
        #response(status, response_headers)
        return([msg])

def main(args):

    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "services"))
    sys.path.insert(0, config.html_dir)

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
    # 5 readers max on this socket...
    listener.listen(5)

    # Starting WebSocket Server/Services/Workers
    gwss.start()

    # Starting network listener
    pool = Pool(config.max_clients)
    gevent.signal(signal.SIGQUIT, gevent.kill)
    gwss.logger.info("gwss:WebSocket Server is listening at http://%s:%s/" % (config.server, config.port))
    gwsgi = WSGIServer((config.server, config.port), gwss_dispatch, spawn=pool, handler_class=WebSocketHandler)
    gwsgi.serve_forever()

    # Trying to exit properly
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
    argparser.add_argument("--server", default=config.server, dest="server", action="store", help="IP address to listen")
    argparser.add_argument("--port", default=config.port, dest="port", action="store", help="Port to use for listen")
    argparser.add_argument("--logfile", default=config.logfile, dest="logfile", action="store", help="File where to write logs")
    argparser.add_argument("--pidfile", default=config.pidfile, dest="pidfile", action="store", help="File where to write PID")
    argparser.add_argument("--sockname", default=config.sockname, dest="sockname", action="store", help="Create socket file")
    args = argparser.parse_args()

    logger = logging.getLogger()
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
    logger.info("gwss:Starting...")
    logger.debug("gwss:Starting (%s)" % args)
    gwss = GWSServer(logger)
    if args.daemon:
        pid = os.fork()
        if pid != 0:
            sys.exit(0)
    sys.exit(main(args))

