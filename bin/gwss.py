#!/usr/bin/env python
from __future__ import print_function
import sys
import json
import os
import time
import logging

from gevent import socket
from geventwebsocket.handler import WebSocketHandler
from gevent.pywsgi import WSGIServer
from gevent.pool import Pool
#from gevent.lock import Semaphore
#from gevent.server import StreamServer
from datetime import datetime

import gevent
import signal
import mimetypes

VERSION = "0.1.0"
server = "gwss.modulix.net"
port = 8888
max_clients = 1000
#html_dir = "~/public_html"
#html_dir = "/var/www/html"
html_dir = "/usr/share/nginx/html"
api_url = "/api"

from threading import Thread
if sys.version_info.major == 2:
	print("running Python 2.x")
	import urlparse

if sys.version_info.major == 3:
	print("running Python 3.x")
	import urllib.parse as urlparse

from WebSocketServer import WebSocketServer
from WebSocketService import WebSocketService
from WebSocketWorker import WebSocketWorker

class GWSHandler():
	def __init__(self, gwss, environ, ws):
		print("GWSHandler(%s) Init" % id(self))
		self.gwss = gwss
		self.ws = ws
		self.environ = environ
		self.listen = True
	def send(self,msg):
		if self.listen and msg:
			self.ws.send(msg)
	def run(self):
		try:
			self.ip = self.environ["HTTP_X_REAL_IP"]
		except:
			self.ip = self.environ["REMOTE_ADDR"]
		self.gwss.add_client(self)
		while self.listen:
			message = self.ws.receive()
			if message is None:
				print("{} socket closed ?! {}".format(datetime.now().strftime("%H:%M:%S"), message))
				self.listen = False
			else:
				print("GWSHandler(%s):receive:%s" % (id(self),message))
				service = action = data = ""
				msg = json.loads(message)
				service = msg["service"]
				action = msg["action"]
				for svc in self.gwss.services:
					if service == svc.name:
						svc.receive(self, message)
		gwss.del_client(self)
	#def __del__(self):
		#print("GWSHandler(%d) dead" % id(self))

def GWSGIHandler(environ, response):
	"""
	For each connection we dispatch to one of this handler:
		WebSocket
		WSGI
	"""
	msg = status = '404 Not found'
	response_headers = [("Content-type", "text/text"), ("Content-Length", str(len(msg)))]
	response(status, response_headers)
	#print("{} GWSGIHandler {}".format(datetime.now().strftime("%H:%M:%S"), environ))
	try:
		if environ["HTTP_CONNECTION"] == "upgrade" and environ["HTTP_UPGRADE"] == "websocket":
			ws = True
		else:
			ws = False
	except:
		ws = False
		pass
	if ws:
		print("GWSGIHandler:%s: opening websocket..." % (environ["PATH_INFO"]))
		ws = environ["wsgi.websocket"]
		wsh = GWSHandler(gwss, environ, ws)
		wsh.run()
	else:
		# WebSocket management API
		if environ["PATH_INFO"][:len(api_url)] == api_url:
			try:
				(prefixe, service, action) = environ["PATH_INFO"][1:].split("/", 2)
				data = environ["QUERY_STRING"]
				print("%s: service=%s action=%s data=%s" % (environ["PATH_INFO"], service, action, data))
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
			print("GWSGIHandler:%s(%s)" % (fname,ext))
			# Directories -> files.py
			if os.path.isfile("%s.py" % fname[:-1]):
				(module, action) = os.path.split(environ["PATH_INFO"][1:])
				module = module.replace("/",".")
				print("GWSGIHandler:DIR:module=%s action=%s" % (module, action))
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
					print("GWSGIHandler:PY:module=%s action=%s" % (module, action))
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
				print("GWSGIHandler:%s Not found"% (file_name))
				msg = status = "404 Not found"
				response_headers = [("Content-type", "text/text"), ("Content-Length", str(len(msg)))]
				response(status, response_headers)
		return([msg])

if __name__ == "__main__":
	"""
	This is a the main of this multi-threaded daemon
	urls = [
		(r"/api/(.*)", ApiHandler),
		(r"/(.*)", SocketHandler),
		]
	"""
	# FS socket && Network socket
	try:
		os.mkdir("/run/gwss")
	except:
		pass
	listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
	sockname = "/run/gwss/gwss.sock"
	if os.path.exists(sockname):
		os.remove(sockname)
	listener.bind(sockname)
	listener.listen(1)

	sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "services"))
	sys.path.insert(0, html_dir)

	##FORMAT = "%(asctime)-15s %(clientip)s %(user)-8s %(message)s"
	##logging.basicConfig(format=FORMAT)
	#d = {"client": "127.0.0.1", "user": "root"}
	#logging.info("gwss: %s", "Starting...", extra=d)
	#logging.info("gwss: %s", "Starting...")
	#logging.info("gwss: %s", __file__)

	gwss = WebSocketServer()
	gwss.start()
	print("gwss:WebSocket Server running at http://%s:%s/" % (server, port))
	gevent.signal(signal.SIGQUIT, gevent.kill)
	pool = Pool(max_clients)
	gwsgi = WSGIServer(("0.0.0.0", 8888), GWSGIHandler, spawn=pool, handler_class=WebSocketHandler)
	gwsgi.serve_forever()
	print("gwss:WebSocket Server stopped.")
	gwss.stop()
	gwss.join()
	del gwsgi
