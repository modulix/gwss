#!/usr/bin/env python
from classes.SimpleService import SimpleService

class EchoService(SimpleService):
	"""
	This service broadcast all received messages to all connected clients
	event -> worker -> send_all (same message)
	"""
	def action_echo(self, client, key):
		self.send_action("clients", "send_client", client=client, js_action="display", data={"key":key})

def echo():
	return EchoService("echo")
