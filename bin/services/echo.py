#!/usr/bin/env python

class EchoService():
	"""
	This service broadcast all received messages to all connected clients
	event -> worker -> send_all (same message)
	"""
	def __init__ (self,service):
		self.service = service
	def action_echo(self, client, data):
		self.service.send_group('*', "display", data)

def echo(service):
	return EchoService(service)
