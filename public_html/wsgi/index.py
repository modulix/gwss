#!/usr/bin/env python
from __future__ import print_function
from datetime import datetime

def index(gwss, environ, response):

	print("{} wsgi.index:index {}".format(datetime.now().strftime("%H:%M:%S"), environ))
	#gevent.spawn(process,ws,data,sem)
	tbl = []
	for (key, value) in environ.iteritems():
		tbl.append("%s: %s" % (key, value))
	output = "<pre>%s</pre>" % ("\n".join(tbl))
	print("wsgi.index:index:%s" % output)
	status = "200 OK"
	response_headers = [("Content-type", "text/html"), ("Content-Length", str(len(output)))]
	response(status, response_headers)
	return(output)

def env(gwss, environ, response):

	print("{} wsgi.index:env {}".format(datetime.now().strftime("%H:%M:%S"), environ))
	#gevent.spawn(process,ws,data,sem)
	tbl = []
	for (key, value) in environ.iteritems():
		tbl.append("%s: %s" % (key, value))
	output = "%s" % ("\n".join(tbl))
	print("wsgi.index:env:%s" % output)
	status = "200 OK"
	response_headers = [("Content-type", "text/text"), ("Content-Length", str(len(output)))]
	response(status, response_headers)
	return(output)
