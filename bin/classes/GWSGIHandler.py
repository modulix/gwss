#!/usr/bin/env python

#from gevent.server import StreamServer

import logging
from webob import Request


class GWSGIHandler():
    """
    WSGI
    """
    def __init__(self, server_name, routes, environ, response):
        self.logger = logging.getLogger(server_name)
        self.name = server_name
        self.environ = environ
        self.response = response
        self.content = []
        ip = self.environ.get("HTTP_X_REAL_IP", self.environ.get("REMOTE_ADDR", "127.0.0.1"))
        self.address = "%s:%s" % (ip, self.environ.get("REMOTE_PORT"))
        self.logger.debug("GWSGIHandler:init:%s" % self.address)
        self.routes = routes

    def run(self):
        self.logger.debug("GWSGIHandler:Answering request %s" % self.environ["PATH_INFO"])
        msg = "Not found"
        status = "404"
        mime = "text/text"
        request = Request(self.environ)
        try:
            trace = self.routes(request)
            if trace.endpoint.annotations.get('static_view'):
                msg = trace.target(request, *trace.args)(self.environ, self.response)
                return msg
            view = trace.target
            args, kwargs = trace.args, trace.kwargs
            kwargs.update({k:v for k,v in request.GET.items()})
            kwargs.update({k:v for k,v in request.POST.items()})
            msg = view(*args, **kwargs)
            status = "200"
        except Exception as e:
            msg = str(e)
        self.response(status, [])
        return msg
