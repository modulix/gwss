#!/usr/bin/env python
from __future__ import print_function
from datetime import datetime

def index(gwss, environ, response):
	tbl = []
	for (key, value) in environ.iteritems():
		tbl.append("%s: %s" % (key, value))
	output = "<pre>%s</pre>" % ("\n".join(tbl))
	status = "200 OK"
	response_headers = [("Content-type", "text/html"), ("Content-Length", str(len(output)))]
	response(status, response_headers)
	return(output)
