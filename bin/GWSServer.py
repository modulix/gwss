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
from gevent import socket
import common.logger

VERSION = "0.4.0"

class GWSServer():
    """
    This server is used to control all services
    found in ./services/ directory
    """
    def __init__(self, conf_path):
        try:
            with open(conf_path) as f:
                all_conf = json.loads(f.read())
                self.config = all_conf["core"]
                self.service_conf = all_conf.get("services", {})
                self.daemon_conf = all_conf.get("daemons", {})
                # We setup root logger, but we won't use it directly. 
                root_logger = common.logger.get_logger_from_config(all_conf.get("logs", []))
        except IOError:
            sys.exit("Unable to read root config. Exiting...")
        # We log in our own logger. It is then propagated to root logger.
        self.logger = common.logger.get_logger_from_config(self.config.get("logs", []), "core")
        self.logger.info("GWSServer init...")
        # PID file (needed when running as service)
        try:
            os.mkdir(os.path.dirname(self.config["pidfile"]))
        except:
            pass
        fd = open(self.config["pidfile"], "w")
        if fd:
            fd.write("%d" % os.getpid())
            fd.close()
        # FS socket
        sockname = self.config["sockname"]
        try:
            os.mkdir(os.path.dirname(sockname))
        except:
            pass
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        if os.path.exists(sockname):
            os.remove(sockname)
            listener.bind(sockname)
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
        service_dir = self.config["service_dir"]
        daemon_dir = self.config["daemon_dir"]
        self.logger.debug("Loading all services in %s :" % service_dir)
        
        # Load all services. One instance for each module.
        for file_name in os.listdir(service_dir):
            (fln, fle) = os.path.splitext(file_name)
            if os.path.isfile(os.path.join(service_dir, file_name)) and fle == ".py" and fln != "__init__":
                self.logger.debug("Service loading : %s" % file_name)
                # Get service ration from ./service/service.py file
                try :
                    module = importlib.import_module("services."+fln)
                    self.logger.debug("Service init start : %s" % fln)
                    # Services are named after their module (file) name
                    service = getattr(module, fln)(self.service_conf.get(fln, {}))
                    self.logger.debug("Service init end : %s" % fln)
                    self.services[fln] = service
                except Exception as e:
                    self.logger.warning("Failed to load service %s" % fln)
                    self.logger.debug(traceback.format_exc())
        # Daemons are different. There is one named instance for each conf for them.
        for daemon_type in self.daemon_conf.keys():
            self.logger.debug("Daemon loading : %s" % daemon_type)
            try :
                module = importlib.import_module("daemons."+daemon_type)
                for daemon_name in self.daemon_conf[daemon_type].keys():
                    self.logger.debug("Daemon init start : %s" % daemon_name)
                    service = getattr(module, daemon_type)(daemon_name, self.daemon_conf[daemon_type][daemon_name])
                    self.logger.debug("Daemon init end : %s" % daemon_name)
                    self.listen_filenos[service.listen_fileno] = service
                    self.daemons[daemon_name] = service
                    self.services[daemon_name] = service
            except Exception as e:
                self.logger.warning("Failed to load daemon %s" % daemon_type)
                self.logger.debug(traceback.format_exc())
        self.logger.debug("GWSServer ready")
        # Give the service awareness from other modules for inter-module communication
        for service in self.services.values():
            service.set_services(self.services)
        while True:
            read_fds, _, _ = select.select(self.listen_filenos.keys(), [], [])
            for fd in read_fds:
                msg = self.listen_filenos[fd].recv_action()
                service = msg.pop("service")
                if service in self.services:
                    self.services[service].add_event(msg)
        self.logger.debug("GWSServer exiting...")

#from gevent.lock import Semaphore
#from gevent.server import StreamServer

def main(conf_path):
    gwss = GWSServer(conf_path)
    gwss.run()
    return(0)

if __name__ == "__main__":
    """
    This is a the main of this multi-threaded daemon
    """
    argparser = argparse.ArgumentParser(prog='gwss')
    argparser.add_argument("--daemon", action="store_true", help="Run in background")
    argparser.add_argument("--config", action="store", help="Main JSON configuration file", dest="config", default="./config.json")
    args = argparser.parse_args()
    if args.daemon:
        pid = os.fork()
        if pid != 0:
            sys.exit(0)
    sys.exit(main(args.config))

