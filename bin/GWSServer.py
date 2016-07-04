#!/usr/bin/env python
from __future__ import print_function
import sys
import os
import select
import time
import json
import argparse
from datetime import datetime, timedelta
from threading import Thread
from multiprocessing import Pipe
import importlib 
import traceback
import logging
import logging.handlers
from gevent import socket

VERSION = "0.4.0"

pidfile = "/home/arthur/gwss/gwss.pid"
sockname = "/home/arthur/gwss/gwss.sock"
logfile = "/home/arthur/gwss/gwss.log"
api_url = "/api"
#html_dir = "~/public_html"
#html_dir = "/usr/share/nginx/html"
html_dir = "/home/arthur/gwss/public_html"
services_dir = "/home/arthur/gwss/bin/services"
daemon_dir = "/home/arthur/gwss/bin/daemons"

class GWSServer():
	"""
	This server is used to control all services
	found in ./services/ directory
	"""
	def __init__(self, args):
		self.logger = logging.getLogger()
		self.logger.setLevel(logging.DEBUG)
		#if self.syslog:
		#	handler = logging.handlers.SysLogHandler(address = '/dev/log')
		#	log_format = logging.Formatter('%(levelname)s %(name)s[%(process)d]:%(asctime)s %(message)s')
		#else:
		handler = logging.FileHandler(args.logfile)
		log_format = logging.Formatter('%(asctime)s %(levelname)s %(name)s[%(process)d]: %(message)s')
		handler.setFormatter(log_format)
		handler.setLevel(logging.DEBUG)
		self.logger.addHandler(handler)
		self.logger.info("GWSServer init...")
		sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "services"))
		sys.path.insert(0, services_dir)
		sys.path.insert(0, daemon_dir)
		sys.path.insert(0, html_dir)

		# FS socket && Network socket
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

		self.services = {}
		self.daemons = {}
		self.listen_filenos = {}
		#sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "services"))
	def sighup(self):
		self.logger.debug("GWSServer receive SIGHUP signal..." )

	def run(self):
		self.logger.debug("GWSServer run...")
		# This server start a service thread for each .py file found in ./services subdirectory
		self.logger.debug("GWSServer starting all services in %s :" % services_dir)
		for file_name in os.listdir(services_dir):
			(fln, fle) = os.path.splitext(file_name)
			if os.path.isfile(os.path.join(services_dir, file_name)) and fle == ".py" and fln != "__init__":
				self.logger.debug("Service loading : %s" % file_name)
		# Get service ration from ./service/service.py file
				try :
					module = importlib.import_module("services."+fln)
					self.logger.debug("Service init start : %s" % fln)
					service = getattr(module, fln)()
					self.logger.debug("Service init end : %s" % fln)
					self.services[fln] = service
				except Exception as e:
					self.logger.info("Failed to load service %s" % fln)
					self.logger.debug(traceback.format_exc())
		for file_name in os.listdir(daemon_dir):
			(fln, fle) = os.path.splitext(file_name)
			if os.path.isfile(os.path.join(daemon_dir, file_name)) and fle == ".py" and fln != "__init__":
				self.logger.debug("Daemon loading : %s" % file_name)
		# Get service ration from ./service/service.py file
				try :
					module = importlib.import_module("daemons."+fln)
					self.logger.debug("Daemon init start : %s" % fln)
					service = getattr(module, fln)()
					self.logger.debug("Daemon init end : %s" % fln)
					self.listen_filenos[service.listen_fileno] = service
					self.daemons[fln] = service
					self.services[fln] = service
				except Exception as e:
					self.logger.info("Failed to load daemon %s" % fln)
					self.logger.debug(traceback.format_exc())
		self.logger.debug("GWSServer ready")
		# Give the service awareness from other modules for inter-module communication
		for service in self.services.values():
			service.set_services(self.services)
		while True:
			read_fds, _, _ = select.select(self.listen_filenos.keys(), [], [])
			for fd in read_fds:
				service, action, data = self.listen_filenos[fd].recv_action()
				if service in self.services:
					self.services[service].add_event(action, data)
		self.logger.debug("GWSServer exiting...")


#from gevent.lock import Semaphore
#from gevent.server import StreamServer

def main(args):
	gwss = GWSServer(args)
	gwss.run()
	return(0)

if __name__ == "__main__":
	"""
	This is a the main of this multi-threaded daemon
	"""
	argparser = argparse.ArgumentParser(prog='gwss')
	argparser.add_argument("--daemon", action="store_true", help="Run in background")
	argparser.add_argument("--syslog", action="store_true", help="Use syslog for logging")
	argparser.add_argument("--logfile", default=logfile, dest="logfile", action="store", help="File where to write logs")
	argparser.add_argument("--pidfile", default=pidfile, dest="pidfile", action="store", help="File where to write PID")
	argparser.add_argument("--sockname", default=sockname, dest="sockname", action="store", help="Create socket file")
	args = argparser.parse_args()
	if args.daemon:
		pid = os.fork()
		if pid != 0:
			sys.exit(0)
	sys.exit(main(args))

